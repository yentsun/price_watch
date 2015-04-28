<%inherit file="base.mako"/>
<%def name="noindex()"><meta name="verify-reformal" content="7eb4a72022cfae60dcf8a022" /></%def>
<%def name="title()">
     % if current_location:
    Цены на продукты, ${current_location}
    % else:
    Цены на продукты
    % endif
</%def>
<%def name="description()">
    Динамика цен на продукты за последний месяц
    % if current_location:
    ${current_location}
    % endif
</%def>
<%def name="location_menu()">
    <%include file="partials/location_menu.mako"
              args="current_location=current_location, locations=locations,
                    current_path='/'" />
</%def>
      <div class="row-fluid marketing">
          <div class="span12">
              % for type_title, type_title_ru, type_color, type_background, categories in types:
                  <style>
                      #${type_title} .table>tbody>tr>td a{
                          color: #${type_color}
                      }
                      #${type_title} .type_title{
                          color: #${type_color}
                  </style>
                  <div class="category_wrapper" id="${type_title}"
                       style="background: #${type_background}">
                      <table class="table">
                      <tbody>
                      <tr>
                          <td class="type_title" colspan="3">
                              ${type_title_ru}
                          </td>
                      </tr>
                          % for url, title, price, delta, package in categories:
                              <tr>
                                  <td>
                                      <a href="${url}">${title}</a>
                                  </td>
                                  <td align="center">
                                          <%include
                           file="partials/price.mako"
                           args="price=price, delta=delta" />
                                  </td>
                                  <td>${package}</td>
                              </tr>
                          % endfor
                      </tbody>
                  </table>
              </div>
              % endfor
              <span title="Время последнего обновления"
                    class="label label-default"
                    style="margin-bottom: 3em">
                  <i class="glyphicon glyphicon-time"></i>
                  ${time}
              </span>
        </div>
      </div>
<%def name="js()">
</%def>