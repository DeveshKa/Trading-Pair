export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const shortDate = date => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
export const number = value => new Intl.NumberFormat('en-IN').format(value);
export const sigma = value => `${value>=0?'+':''}${value.toFixed(2)}σ`;
export function filterPairs(pairs, state, saved = new Set()) {
  const query=(state.query||'').trim().toLowerCase();
  return pairs.filter(p => (!query || [p.a.symbol,p.b.symbol,p.a.name,p.b.name].some(s=>s.toLowerCase().includes(query))) &&
    (!state.exchange || p.a.exchange===state.exchange || p.b.exchange===state.exchange) &&
    (!state.gap || (state.gap==='divergence' ? Math.abs(p.gap_z)>=2 : Math.abs(p.gap_z)<2)) &&
    (!state.savedOnly || saved.has(p.id)) && p.distance<=Number(state.maxDistance??Infinity))
    .sort((a,b)=>state.sort==='gap'?Math.abs(b.gap_z)-Math.abs(a.gap_z):state.sort==='history'?b.valid_cohorts-a.valid_cohorts:a.rank-b.rank);
}
export function csvFor(pairs) {
  const cell=s=>{let v=String(s??'');if(typeof s==='string'&&/^[=+\-@\t\r]/.test(v))v="'"+v;return '"'+v.replaceAll('"','""')+'"';};
  return [['Rank','Stock A','Company A','Stock B','Company B','Formation date','Mean SSD','Formation gap sigma','Observed cohorts','Execution ready'],
    ...pairs.map(p=>[p.rank,p.a.symbol,p.a.name,p.b.symbol,p.b.name,p.formed_at,p.distance,p.gap_z,p.cohorts,'No'])].map(r=>r.map(cell).join(',')).join('\r\n');
}
export function validateBundle(b) {
  if(!b || b.schema_version!==1 || !Array.isArray(b.horizons) || !b.horizons.length || typeof b.as_of!=='string') throw Error('Choose a Pairwise dashboard bundle (schema version 1).');
  const date=s=>typeof s==='string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s));
  if(!date(b.as_of) || !date(b.data_start) || !date(b.data_end))throw Error('Invalid snapshot dates.');
  const countValue=n=>Number.isInteger(n)&&n>=0;
  if(typeof b.snapshot!=='string'||typeof b.source!=='string'||['observations','observed_stocks','study_cohorts'].some(k=>!countValue(b[k])))throw Error('Invalid snapshot metadata.');
  let count=0;
  for(const h of b.horizons) {
    if(!Number.isInteger(h.sessions)||h.sessions<1||!Array.isArray(h.pairs)||h.pairs.length>5000||!countValue(h.eligible)||!countValue(h.comparisons)||typeof h.label!=='string'||!Array.isArray(h.audit)) throw Error('Invalid horizon.');
    if(h.audit.some(a=>typeof a.symbol!=='string'||typeof a.reason!=='string'||!Number.isFinite(a.median_turnover_inr)))throw Error('Invalid data audit.');
    const ids=new Set();
    for(const p of h.pairs) {
      if(typeof p.id!=='string'||ids.has(p.id)||!p.a||!p.b||!Number.isFinite(p.distance)||p.distance<0||!Number.isFinite(p.gap_z)||!Array.isArray(p.series)||p.series.length<2) throw Error('Invalid pair evidence.');
      ids.add(p.id);
      if(['rank','cohorts','valid_cohorts','openings','crossings','unresolved'].some(k=>!countValue(p[k]))||['sigma','gap_percent','sum_distance'].some(k=>!Number.isFinite(p[k]))||!date(p.formed_at)||!date(p.formation_start))throw Error('Invalid pair statistics.');
      for(const leg of [p.a,p.b]) if(['symbol','ticker','name','exchange','isin'].some(k=>typeof leg[k]!=='string'))throw Error('Missing security identity.');
      if(!Array.isArray(p.history)||p.history.some(o=>!date(o.formed_at)||['opened','converged','unresolved','forward_sessions'].some(k=>!countValue(o[k]))||typeof o.window_complete!=='boolean'))throw Error('Invalid historical observations.');
      if(p.series.some(s=>!date(s.date)||['a','b','spread','z'].some(k=>!Number.isFinite(s[k]))))throw Error('Invalid chart series.');
      count+=p.series.length;
    }
  }
  if(count>250000)throw Error('Bundle has too many chart observations. Export a smaller research selection.');
  if(!b.quality || !Array.isArray(b.quality.notes)||!b.quality.notes.every(n=>typeof n==='string')||!countValue(b.quality.unresolved_volume_cases))throw Error('Quality notes are required.');
  if(typeof b.synthetic!=='boolean'||['membership_audited','actions_complete','bse_loaded','live_feed_connected'].some(k=>typeof b.quality[k]!=='boolean'))throw Error('Quality flags must be boolean.');
  return b;
}
export function chartGeometry(series, keys, width=600, height=210) {
  const values=series.flatMap(s=>keys.map(k=>s[k]));
  let low=Math.min(...values),high=Math.max(...values); const pad=Math.max((high-low)*.13,.3);low-=pad;high+=pad;
  const x=i=>42+i/Math.max(series.length-1,1)*(width-54),y=v=>14+(high-v)/(high-low)*(height-42);
  return {low,high,x,y,paths:Object.fromEntries(keys.map(k=>[k,series.map((s,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(s[k]).toFixed(2)}`).join(' ')]))};
}
