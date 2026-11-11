export function fixture(){
 const pairs=Array.from({length:12},(_,i)=>({id:`S${i}A|S${i}B`,rank:i+1,
 a:{symbol:`S${i}A.NS`,ticker:`S${i}A`,name:`Aster company ${i}`,exchange:'NSE',isin:`TESTA${i}`},
 b:{symbol:`S${i}B.NS`,ticker:`S${i}B`,name:`Birch company ${i}`,exchange:'NSE',isin:`TESTB${i}`},
 distance:.001*(i+1),sum_distance:.252*(i+1),sigma:.02,gap_z:i/2-2,gap_percent:i-4,
 formed_at:'2024-01-20',formation_start:'2024-01-01',execution_ready:false,state:'watching',
 cohorts:1,valid_cohorts:1,openings:2,crossings:1,unresolved:1,
 series:Array.from({length:20},(_,j)=>({date:`2024-01-${String(j+1).padStart(2,'0')}`,a:100+j,b:100+j*.9,spread:j*.1,z:j*.05})),
 history:[{a:`S${i}A.NS`,b:`S${i}B.NS`,formed_at:'2023-01-01',forward_sessions:126,window_complete:true,opened:2,converged:1,unresolved:1,status:'OK'}]}));
 return {schema_version:1,snapshot:'fixture-only',source:'synthetic_demo',synthetic:true,as_of:'2024-01-20',data_start:'2023-01-01',data_end:'2024-01-20',observations:4000,observed_stocks:24,study_cohorts:12,
 horizons:[{sessions:252,label:'1Y formation',eligible:24,comparisons:276,pairs,audit:[]},{sessions:756,label:'3Y formation',eligible:20,comparisons:190,pairs:pairs.slice(0,4),audit:[]}],
 quality:{membership_audited:false,actions_complete:false,unresolved_volume_cases:3,bse_loaded:false,live_feed_connected:false,notes:['Synthetic fixtures only.']}};
}
