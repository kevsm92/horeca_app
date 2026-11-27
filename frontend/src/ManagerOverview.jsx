import React from 'react';
import {demoDashboardMetrics,displayMetric} from './dashboardMetrics.js';
import './managerOverview.css';
export default function ManagerOverview({tables,orders,orderValueCents,onTables,onOrders}) {
  const metrics=demoDashboardMetrics({tables,orders,orderValueCents}).map(displayMetric);
  return <section aria-labelledby="manager-overview-title" className="manager-overview">
    <div className="manager-overview-heading"><div><h2 id="manager-overview-title">Manager overview</h2><p>Fictional venue preview. Live workforce and financial totals are not connected.</p></div><span className="manager-overview-mode">DEMO · NOT LIVE</span></div>
    <div className="manager-overview-metrics">{metrics.map(metric=><article key={metric.id} className="manager-overview-metric"><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.status}</small><p>{metric.detail}</p></article>)}</div>
    <div className="manager-overview-actions"><button type="button" onClick={onTables}>Open floor plan</button><button type="button" onClick={onOrders}>Take order</button></div>
    <p className="manager-overview-note">Scheduled shifts never establish actual presence. Demo order value does not represent captured revenue. No historical chart is shown without verified historical records.</p>
  </section>;
}
