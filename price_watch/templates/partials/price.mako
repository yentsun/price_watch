<%page args="price, delta=None"/>
% if delta:
    % if delta > 0:
        <span title="+${delta}%"
              style="color:red">
            % if delta > 50:
            ▲
            % else:
            ▴
            % endif
        </span>
    % elif delta < 0:
        <span title="-${delta}%"
              style="color:green">
            % if delta > 50:
            ▼
            % else:
            ▾
            % endif
        </span>
    % endif
% endif
<span itemprop="price" class="price_value">${price}</span>
<i class="fa fa-rub"></i>
<span class="currency_iso"
      itemprop="currency">RUB</span>