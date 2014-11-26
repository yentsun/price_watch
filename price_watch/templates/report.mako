<%inherit file="base.mako"/>
      <div>
        <h1><%block name="title">${req.context.key}</%block>:
        </h1>
      </div>

      <hr>

      <div class="row-fluid marketing">
          <div class="span12">
              ${req.context}
        </div>
      </div>