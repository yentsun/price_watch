<h2>Прислано отчетов: ${counts['total']}</h2>
<p>Авторы: ${reporters}</p>
<h3>Добавлено в базу</h3>
<table>
    <tbody>
        <tr>
            <td>отчетов</td><td>${counts['report']}</td>
        </tr>
        <tr>
            <td>продуктов</td><td>${counts['product']}</td>
        </tr>
    </tbody>
</table>
<h3>Ошибки: ${counts['error']}</h3>
% for msg in error_msgs:
<p>${msg}</p>
% endfor