/**
 * Created by Steve on 10.08.2016.
 */

var whattodoApp = angular.module('whattodo_app', []);


whattodoApp.run(function($rootScope, $http, $timeout) {
    angular.extend($rootScope, {
        update_list: function (list, new_element) {
            for(var i=0;list.length>i;i++){
                if(list[i]['id'] == new_element['id']){
                    list[i] = new_element
                }
            }
        },
        delete_element: function (list, element) {
            for(var i=0;list.length>i;i++){
                if(list[i]['id'] == element['id']){
                    list.splice(i, i+1)
                }
            }
        },
        init: function () {
            $rootScope.$$childTail.$$prevSibling.loading = true;
            return $http({ method: 'POST',url: window.location.pathname}).then(function successCallback(response) {
                console.log(response)
                if(response.data.hasOwnProperty('dict_data')){
                    $rootScope.$$childTail.$$prevSibling.dict_data = response.data.dict_data;
                    $rootScope.$$childTail.$$prevSibling.data = response.data.data;
                }else{
                    $rootScope.$$childTail.$$prevSibling.data = response.data.data;
                    $rootScope.$$childTail.$$prevSibling.addt_data = [];
                    for(var key in response.data){
                        if(key != 'data'){
                           $rootScope.$$childTail.$$prevSibling.addt_data[key] = response.data[key]
                        }
                    }
                }
                $rootScope.$$childTail.$$prevSibling.loading = false;
            }, function errorCallback(response) {
            });
        },
        loadNextPage: function (url, after_load) {
            var lnpf = function (onscroll) {
                var atend = onscroll ?
                    ($(window).scrollTop() >= $(document).height() - $(window).height() - 10) :
                    (($(document).height() - $(window).height() === 0));
                if (atend && !scope.loading && !scope.data.end) {
                    scope.next_page += 1;
                    scope.loading = true;
                    load();
                }
            }
            var scope = this;
            scope.next_page = 1;
            $(window).scroll(function () {
                if (scope.scroll_data) {
                    scope.scroll_data.next_page = scope.next_page
                }
                lnpf(true);
            });
        
            $timeout(lnpf, 500);
            var load = function () {
                $ok(url, scope.scroll_data ? scope.scroll_data : {next_page: scope.next_page}, function (resp) {
                    scope.data.end = resp.end;
                    after_load(resp);
                    scope.loading = false;
                }).finally(function () {
                    $timeout(function () {
                        lnpf();
                    }, 1000)
                });
            }
        },
        errorHandler: function(data, miliseconds) {
            if(!miliseconds) {
                miliseconds = 1000
            }
            if('error' in data){
                $rootScope.$$childTail.error = data.error
            }
            if('success' in data){
                $rootScope.$$childTail.success = data.success
            }
            $timeout(function () {
                $rootScope.$$childTail.error = '';
                $rootScope.$$childTail.success = '';
            }, miliseconds)
        }
    })

});


whattodoApp.directive('pfDate', function () {
        return {
            replace: false,
            restrict: 'A',
            scope: {
                pfDate: '='
            },
            link: function (scope, element, attrs, model) {
                if(scope['pfDate'] === null){
                    element.text('Present')
                }else{
                    element.text(scope['pfDate'])
                }
                scope.$watch('pfDate', function (nv, ov) {
                    scope.setdate = scope['pfDate'];
                });
                scope.$watch('setdate', function (nv, ov) {
                    if (nv && nv.setHours) nv.setHours(12);
                    scope['ngModel'] = nv;
                });
            }
        }
}).directive('pfRequired', function ($timeout) {
        return {
            replace: false,
            restrict: 'A',
            scope: {
                ngModel: '='
            },
            link: function (scope, element, attrs, model) {

                var Error = false;
                element.click(function(){
                    errorMsg(element)
                });

                scope.$watch('ngModel', function (nv, ov) {
                    if(isEmpty(scope['ngModel'])){
                        element.addClass('invalid');
                    }else{
                        element.removeClass('invalid')
                    }
                });

                function errorMsg(element) {
                    if(!Error && isEmpty(element.context.value)){
                        element.after('<span id="error-msg">'+'Fill out required fields - `'+ attrs.ngModel.split('.')[1]+'`!'+'</span>');
                        Error = true;
                        $timeout(function () {
                            $('#error-msg').remove();
                            Error = false
                        }, 1500)
                    }
                }
            }
        }
}).directive('pfSave', function ($http, $timeout) {
        return {
            replace: false,
            restrict: 'A',
            scope: {
                pfSave: '=',
                pfRequiredFields: '=',
                pfAfterSave: '=',//must be callable
                pfBeforeSave: '='//must be callable
            },
            link: function (scope, element, attrs, model) {
                
                var buttonDOMElement = document.querySelector('#'+attrs['id']);

                var button = angular.element(buttonDOMElement);

                var onButtonClick = function () {
                    scope.$parent.loading = true;
                    var url = scope['pfSave'].hasOwnProperty('id')?window.location.pathname+'?edit': window.location.pathname+'?add';
                    var modal = $('#'+getModalId());
                    if(scope['pfBeforeSave'])
                        scope['pfBeforeSave'](scope['pfSave']);
                    $timeout(function () {
                        if(ifAllow() === true){
                       return $http({ method: 'PUT',url: url, data: scope['pfSave']}).then(function successCallback(response) {
                           if(response.data.error !== 'false'){
                               error_msg(response.data.error)
                           }else{
                               if(scope['pfAfterSave'])
                                   scope['pfAfterSave'](scope['pfSave']);
                               if(modal){
                                   $timeout(function () {
                                      modal.modal('hide')
                                   }, 500)
                               }
                               var up_data = response.data.hasOwnProperty('dict_data')? response.data.dict_data.data: response.data.data;
                               if($.isArray(scope.$parent.data)){
                                   if(scope['pfSave'].hasOwnProperty('id')){
                                        scope.$parent.update_list(scope.$parent.data, up_data)
                                   }else {
                                        scope.$parent.data.push(up_data)
                                   }
                               }else {
                                   scope.$parent.data = up_data;
                               }
                           }
                           if('success' in response.data && response.data.success !== 'true')
                               flash(response.data.success);
                           loading_false()
                       }, function errorCallback() {
                           flash('Server error!')
                       });
                    }else{
                        scope.$parent.loading = false;
                        $timeout(function () {
                            error_msg('Fill out required fields!')
                        },100);
                    }
                    }, 500)

                };

                function loading_false(){
                    $timeout(function () {
                        scope.$parent.loading = false
                    }, 2000)
                }

                function error_msg(msg) {
                    scope.$parent.err = msg;
                    $timeout(function () {
                        scope.$parent.err = ''
                    }, 1000)
                }
            
                button.on('click', onButtonClick);
            
                scope.$on('$destroy', function () {
                    button.off('click', onButtonClick);
                });

                function getModalId() {
                    var id = attrs['id'].split('_')[1];
                    if(id)
                        return 'add'+id.capitalizeFirstLetter();
                }
                
                function ifAllow() {
                    return check_required_fields(scope.$parent.required_fields, scope['pfSave'])
                }
            }
        }
});
whattodoApp.factory('socket', function ($rootScope) {
  var socket = io.connect('http://192.168.0.25:8888');
    socket.on('error', function() {
        socket.disconnect()
    });
  return {
    on: function (eventName, callback) {
      socket.on(eventName, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {

            console.log(callback)
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    }
  };
});


function callBackAfterReadFile(file, data) {
    if(file){
        var fr = new FileReader();
        fr.onload = function (e) {
            data['file'] = {'mime': file.type, 'name': file.name, 'content': fr.result}
            return 'SUCCESS'
        };
        fr.onerror = function (e) {
            flash('File loading error');
        };
        fr.readAsDataURL(file);
    }
}

function check_required_fields(list_of_r_fields, pass_fields) {
    for(var i=0;list_of_r_fields.length>i;i++){
        if(pass_fields.hasOwnProperty(list_of_r_fields[i])){
            if(isEmpty(pass_fields[list_of_r_fields[i]]))
                return 'Fill in '+ list_of_r_fields[i]
        }else{
            return 'Fill in required fields!'
        }
    }
    return true
}

function chech_date_from_to(from, to) {
    if(!from){
       flash('Fill in `from` date!');
        return false 
    }
    if(from>=to){
        flash('First date must be smaller than first!');
        return false
    }
    return true
}

function flash(message) {
    $(".flash").remove();
    $('body').prepend(
        '<div class="flash">' +
            message +
        '</div>'
    );
    $(".flash").delay(4000).fadeOut();
}

function isEmpty(element) {
    return element === '' || element === 0 || element === null
}

String.prototype.capitalizeFirstLetter = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

function now() {
    return Date.now() / 1000;
}

var inactivityTime = function () {
    var t;
    window.onload = resetTimer;
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;

    function logout() {
        console.log("You are now logged out.");
        //location.href = 'logout.php'
    }

    function resetTimer() {
        clearTimeout(t);
        t = setTimeout(logout, 15000);
        // 1000 milisec = 1 sec
    }
};

inactivityTime();

$.fn.scrollTo = function () {
    return this.each(function () {
        $('html, body').animate({
            scrollTop: $(this).offset().top
        }, 1000);
    });
};

function scrool($el) {
    console.log($el)
    $($el).scrollTo();
}




function scrool_to_bottom($el, height) {
    console.log(window.screen.height);
    $($el).animate({ scrollTop: height}, 200);
}