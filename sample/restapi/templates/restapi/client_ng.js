
angular.module('restapi', [])
  .service('API', function ($http) {
    var API = {
      __make_call: function (url, params, callback) {
        $http.post(url, params).success(function (data) {
          if (callback) {
            callback(null, data);
          }
        }).error(function (data, status) {
          if (callback) {
            if (status >= 500) {
              callback(500);
            }
            else {
              callback(status, data);
            }
          }
        });
      }
    };

    {% for group, api_table in apis.iteritems %}

    var {{ group }} = {};
    {% for name, spec in api_table.iteritems %}
    {{ group }}.{{ name }} = function ({% for param in spec.spec.params%}{{ param.name }}, {% endfor %}callback) {
      var params = {};
      {% for param in spec.spec.params%}params.{{ param.name }} = {{ param.name }};
      {% endfor %}
      API.__make_call('{% if group %}{{ group }}/{% endif %}{{ name }}/', params, callback);
    };

    {% endfor %}

    {% if group %}
    API.{{ group }} = {{ group }};
    {% else %}
    for (var api in {{ group }}) {
        API[api] = {{ group }}[api];
    }
    {% endif %}

    {% endfor %}

    return API;
  });