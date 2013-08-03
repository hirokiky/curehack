${form|n}
<ul>
    % for precure in precures:
        <h3>${precure['name']}</h3>
        <p>${precure['description']}</p>
    % endfor
</ul>
