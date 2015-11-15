<%page args="current_location, locations, current_path"/>
% if len(locations):
    <div id="location_menu" class="dropdown">
        <button class="btn btn-default dropdown-toggle"
                type="button" id="locations"
                data-toggle="dropdown" aria-expanded="true">
            % if current_location:
                ${current_location}
            % else:
                Все города
            % endif
            <span class="caret"></span>
        </button>
        <ul class="dropdown-menu" role="menu"
            aria-labelledby="locations">
            % for location in locations:
                <li role="presentation">
                    <a  role="menuitem" tabindex="-1"
                        href="${current_path}?location=${location}">
                        ${location}
                    </a>
                </li>
            % endfor
            <li role="presentation" class="divider"></li>
            <li role="presentation">
                <a  role="menuitem" tabindex="-1"
                    href="${current_path}">Все города
                </a>
            </li>
        </ul>
    </div>
% endif