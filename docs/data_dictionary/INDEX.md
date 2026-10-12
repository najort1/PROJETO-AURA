# Dicionário de dados (gerado)

> Gerado automaticamente a partir de `schemas/*.yaml` por `python tasks.py dictionary`.
> Não edite à mão — edite o contrato e regenere.

| Tabela | Granularidade | Produzida por | Consumidores | Colunas |
|---|---|---|---|---|
| [`agent_input`](agent_input.md) | um registro por cliente na coorte de retenção | ml (features, clv, churn, segmentation/personas, sentiment) | agent.pipeline, agent.eligibility, agent.composer, app | 17 |
| [`anac_airports`](anac_airports.md) | um aeródromo (código OACI) | ingestion.curate | synthetic.generate, snowflake, ml.fairness, app | 9 |
| [`anac_delays_monthly`](anac_delays_monthly.md) | um mês | ingestion.curate | synthetic.generate, snowflake, ml.sentiment, app | 8 |
| [`anac_routes_monthly`](anac_routes_monthly.md) | uma rota (origem-destino OACI) por mês | ingestion.curate | synthetic.generate, snowflake, ml.impact, app | 18 |
| [`churn_predictions`](churn_predictions.md) | um cliente na coorte de teste/avaliação | ml.churn.train | ml.segmentation, agent.pipeline, app, docs.model_cards | 5 |
| [`clv_predictions`](clv_predictions.md) | um cliente na coorte de teste/avaliação | ml.clv.train | ml.segmentation, agent.pipeline, app, docs.model_cards | 7 |
| [`customer_timeline`](customer_timeline.md) | um evento por cliente | ml.segmentation.score_av | app.views.03_cliente_360 | 6 |
| [`customers_scores`](customers_scores.md) | um registro por cliente na coorte de análise | ml.segmentation.score_av | app.views.01_carteira, app.views.03_cliente_360, app.views.04_agente, app.views.06_simulador | 24 |
| [`fairness_metrics`](fairness_metrics.md) | um registro por grupo demográfico em cada dimensão sensível | ml.fairness.audit | app.views.07_ia_responsavel, docs.responsible_ai | 8 |
| [`features_customer`](features_customer.md) | um cliente | dbt: marts.features_customer | ml.clv, ml.churn, ml.segmentation, agent.input, app | 32 |
| [`friction_map`](friction_map.md) | um aspecto por semestre | ml.sentiment.friction_map | synthetic.generate, agent.pipeline, app, ml.impact | 13 |
| [`ground_truth`](ground_truth.md) | um registro por cliente sintético | synthetic.generate | evaluation_only | 13 |
| [`personas_summary`](personas_summary.md) | uma linha por persona catalogada | ml.segmentation.personas | app.views.01_carteira, app.views.02_personas | 12 |
| [`agent_recommendations`](agent_recommendations.md) | uma recomendação por cliente por campanha de retenção | agent.pipeline | app, ml.impact | 12 |
| [`score_av`](score_av.md) | um registro por cliente na coorte de análise | ml.segmentation.score_av | ml.segmentation, agent.pipeline, app | 7 |
| [`segments`](segments.md) | um registro por cliente na coorte de análise | ml.segmentation.cluster | ml.segmentation.personas, agent.pipeline, app | 5 |
| [`sentiment_reviews`](sentiment_reviews.md) | uma avaliação | ml.sentiment.corpus | ml.sentiment.approaches, ml.sentiment.friction_map, ml.sentiment.pipeline | 22 |
| [`synthetic_customers`](synthetic_customers.md) | um registro por cliente sintético | synthetic.generate | dbt: curated -> analytics, ml.fairness, synthetic.fidelity_report | 9 |
| [`synthetic_flights`](synthetic_flights.md) | um voo por trecho operado | synthetic.generate | dbt: curated -> analytics, synthetic.fidelity_report | 11 |
| [`synthetic_interactions`](synthetic_interactions.md) | uma interação | synthetic.generate | dbt: curated -> analytics, synthetic.fidelity_report, ml.churn, agent.pipeline | 9 |
| [`synthetic_loyalty_events`](synthetic_loyalty_events.md) | um evento de fidelidade por ocorrência | synthetic.generate | dbt: curated -> analytics, synthetic.fidelity_report, agent.eligibility | 10 |
| [`synthetic_transactions`](synthetic_transactions.md) | uma transação | synthetic.generate | dbt: curated -> analytics, synthetic.fidelity_report, ml.clv | 10 |
