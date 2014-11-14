<!DOCTYPE html>
<html lang="${req.locale_name}">
<head>
    <meta charset="utf-8">
    <%def name="project_title()">The Price Watch</%def>

    <title>${self.title()} - ${project_title()}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="Max Korinets">

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
            <li class="active"><a href="#">Home</a></li>
            <li><a href="#">About</a></li>
            <li><a href="#">Contact</a></li>
        </ul>
        <h3 class="muted">Price Watch</h3>
    </div>

    <hr>
    ${self.body()}
    <hr>

    <div class="footer">
        <p>&copy; ${project_title()} 2014</p>
    </div>

</div> <!-- /container -->
    % if hasattr(self,'js'):
        ${self.js()}
    % endif
</body>
</html>
