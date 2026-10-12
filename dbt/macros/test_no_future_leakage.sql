{% test no_future_leakage(model, column_name, cutoff_var='cutoff') %}
{#-
    Teste genérico customizado de anti-vazamento temporal.
    Falha alto (retorna linhas) se qualquer data na coluna de data for
    estritamente posterior ao marco de corte (var cutoff).
-#}
SELECT
    {{ column_name }} AS data_evento,
    DATE '{{ var(cutoff_var) }}' AS data_limite_cutoff
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
  AND {{ column_name }} > DATE '{{ var(cutoff_var) }}'
{% endtest %}
