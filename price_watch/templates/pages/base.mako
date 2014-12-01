<%inherit file="../base.mako"/>
<div>
    <h1>${self.title()}</h1>
</div>

<hr>

<div class="row-fluid marketing">
    <div class="span12">
        ${self.body()}
    </div>
</div>