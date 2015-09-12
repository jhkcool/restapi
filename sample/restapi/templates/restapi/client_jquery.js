
(function ($) {
  var API = {
    __make_call: function (url, params, callback) {
      $.ajax(url, {
        method: 'POST',
        dataType: 'json',
        headers: {
            'Content-Type': 'application/json'
        },
      data: JSON.stringify(params)
      }).success(function (data) {
        if (callback) {
          callback(null, data);
        }
      }).fail(function (data) {
        if (callback) {
          if (data.status >= 500) {
            callback(500);
          }
          else {
            callback(data.status, JSON.parse(data.responseText));
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

  $.API = API;
})(jQuery);
