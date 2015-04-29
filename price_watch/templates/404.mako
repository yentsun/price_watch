<%inherit file="base.mako"/>
<%def name="description()">Страница не найдена, приносим свои извинения...</%def>
<div>
    <h1><%block name="title">Страница не найдена (404)</%block></h1>
</div>
<div class="row-fluid marketing">
    <div class="span12">
        <img class="major_image" width="299" height="183"
             src="${request.static_url('price_watch:static/img/404.png')}"
             alt="Тележка сломалась!"/>
    </div>
</div>