<!DOCTYPE html>
<html lang="${req.locale_name}">
<head>
    <meta charset="utf-8">
    <%def name="project_title()">food-price.net</%def>

    <title>${self.title()} - ${project_title()}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="Max Korinets">
    <link rel="shortcut icon" type="image/png"
          href="${request.static_url('price_watch:static/favicon.png')}"/>
    <!-- Le styles -->
    <link href="${request.static_url('price_watch:static/css/'
    'bootstrap.min.css')}"
          rel="stylesheet">
    <link href="${request.static_url('price_watch:static/css/'
    'bootstrap-responsive.min.css')}"
          rel="stylesheet">
    <link href="${request.static_url('price_watch:static/css/theme.css')}"
          rel="stylesheet">
    <!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="../assets/js/html5shiv.js"></script>
    <![endif]-->
</head>

<body>

<div class="container-narrow">

    <div class="masthead">

        <ul class="nav nav-pills pull-right">
            % for title, path, active in view.menu():
            % if active:
            <li class="active">
            % else:
            <li>
                % endif
                <a href="${path}">${title}</a>
            </li>

            % endfor
        </ul>
        <img src="${request.static_url('price_watch:static/img/logo.png')}"
             alt="Логотип" width="230"/>
    </div>

    <hr>
    ${next.body()}
    <hr>

    <div class="footer">
        <p class="pull-right">
            email: <a href="mailto:info@food-price.net">info@food-price.net</a>
        </p>
        <p>&copy; ${project_title()} 2014</p>
    </div>

</div> <!-- /container -->
    % if hasattr(self,'js'):
        ${self.js()}
    % endif
</body>
</html>
