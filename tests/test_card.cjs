/* Dependency-free rendering checks; HA component integration needs live testing. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
 attachShadow(){this.shadowRoot={innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null,append:()=>{}};}
 addEventListener(type,fn){this.listeners={...this.listeners,[type]:fn};}
 dispatchEvent(event){this.event=event;}
}
const registry=new Map();
const context={HTMLElement:Element,customElements:{get:key=>registry.get(key),define:(key,value)=>registry.set(key,value)},window:{},document:{createElement:key=>new (registry.get(key)||Element)()},CustomEvent:class{constructor(type,options){this.type=type;Object.assign(this,options);}},console};
vm.runInNewContext(fs.readFileSync('custom_components/radon_monitor/www/radon-monitor-card.js','utf8'),context);
const Card=registry.get('radon-monitor-card');const card=new Card();
assert.throws(()=>card.setConfig({}),/Select/);
card.setConfig({entity:'sensor.radon_monitor_concentration',name:'<img onerror="evil">',show_graph:false,show_coverage:true});
let states={'sensor.radon_monitor_concentration':{state:'36',attributes:{unit_of_measurement:'Bq/m³'}},'sensor.radon_monitor_status':{state:'normal',attributes:{}},'sensor.radon_monitor_7_days_average':{state:'27.87',attributes:{bucket_coverage_percent:99.68,partial:false}},'binary_sensor.radon_monitor_sensor_problem':{state:'off',attributes:{}}};
card.hass={states};let html=card.shadowRoot.innerHTML;
assert.match(html,/99.7% hourly coverage/);assert.match(html,/27.87/);assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<img onerror/);assert.match(html,/>Normal</);
assert.equal(card.entity('sustained_high_radon'),'binary_sensor.radon_monitor_sustained_high_radon');
card.more('sensor.radon_monitor_7_days_average');assert.equal(card.event.type,'hass-more-info');assert.equal(card.event.detail.entityId,'sensor.radon_monitor_7_days_average');assert.equal(card.event.composed,true);
states['sensor.radon_monitor_7_days_average'].attributes.partial=true;
states['sensor.radon_monitor_status'].state='high';states['binary_sensor.radon_monitor_sustained_high_radon']={state:'on',attributes:{}};card.hass={states};
assert.match(card.shadowRoot.innerHTML,/Partial history/);assert.match(card.shadowRoot.innerHTML,/>High</);assert.match(card.shadowRoot.innerHTML,/>Active</);
states['sensor.radon_monitor_concentration'].state='unavailable';card.hass={states};assert.match(card.shadowRoot.innerHTML,/>Sensor problem</);assert.doesNotMatch(card.shadowRoot.innerHTML,/NaN/);
states['sensor.radon_monitor_concentration'].state='0';card.hass={states};assert.match(card.shadowRoot.innerHTML,/class="reading">0</);
card.setConfig({entity:'sensor.room_concentration',status_entity:'sensor.custom_status',show_graph:false});assert.equal(card.entity('status'),'sensor.custom_status');assert.equal(card.entity('1_year_average'),'sensor.room_1_year_average');
const Editor=registry.get('radon-monitor-card-editor');const editor=new Editor();editor.setConfig({entity:'sensor.room_concentration'});editor.hass={states};assert.equal(editor.form.data.entity,'sensor.room_concentration');assert.ok(editor.form.schema.find(s=>s.name==='advanced').schema.some(s=>s.name==='2_years_average_entity'));
card.setConfig({entity:'sensor.room_concentration',show_graph:false});card.hass={states};assert.match(card.shadowRoot.innerHTML,/--ha-card-background:#082c4c/);
card.setConfig({entity:'sensor.room_concentration',appearance:'theme',show_graph:false});card.hass={states};assert.doesNotMatch(card.shadowRoot.innerHTML,/--ha-card-background:#082c4c/);
assert.equal(context.window.customCards.length,1);
console.log('Card rendering checks passed: valid/zero/missing values, alerts, partial coverage, escaping, entity overrides, editor and more-info event.');
(async()=>{
 const stable=new Card();stable.setConfig({entity:'sensor.test_concentration',show_graph:true});
 let creates=0, mounts=0, resets=0;
 let graphUpdates=0;const configs=[];const graphNode={firstElementChild:null,replaceChildren(...children){mounts++;this.firstElementChild=children[0]||null;}};
 const details={open:false};const body={innerHTML:'',querySelector:s=>s==='.radon-info'?details:null};const style={textContent:''};
 stable.shadowRoot.querySelector=selector=>selector==='#graph'?graphNode:selector==='.body'?body:selector==='style'?style:null;
 let finishHelpers;context.window.loadCardHelpers=()=>new Promise(resolve=>{finishHelpers=resolve;});
 let fixture={'sensor.test_concentration':{state:'44',attributes:{source:'sensor.source'}},'sensor.source':{state:'44',attributes:{}}};
 stable.hass={states:fixture};stable.hass={states:{...fixture,'sensor.other':{state:'1'}}};
 assert.equal(mounts,1); // pending graph cleared once; unrelated update skipped
 fixture={...fixture,'sensor.test_concentration':{state:'45',attributes:{source:'sensor.source'}}};stable.hass={states:fixture};
 assert.equal(mounts,1); // no second graph request while helpers are pending
 finishHelpers({createCardElement:config=>{creates++;configs.push(config);return {set hass(value){graphUpdates++;}};}});await new Promise(resolve=>setImmediate(resolve));
 assert.equal(creates,1);assert.equal(mounts,2);assert.equal(graphUpdates,1);const graph=graphNode.firstElementChild;
 details.open=true;fixture={...fixture,'sensor.test_concentration':{state:'46',attributes:{source:'sensor.source'}}};stable.hass={states:fixture};await new Promise(resolve=>setImmediate(resolve));
 assert.equal(graphNode.firstElementChild,graph);assert.equal(mounts,2);assert.equal(details.open,true);assert.equal(graphUpdates,1);const resetMounts=mounts;stable.setConfig({entity:'sensor.test_concentration',show_graph:true});assert.equal(mounts,resetMounts);
 stable.selectedDays=730;context.window.loadCardHelpers=async()=>({createCardElement:config=>{creates++;configs.push(config);return {set hass(value){graphUpdates++;}};}});stable.render();await new Promise(resolve=>setImmediate(resolve));assert.equal(creates,2);assert.equal(configs[1].days_to_show,730);assert.equal(configs[1].period,'day');assert.notEqual(graphNode.firstElementChild,graph);stable.hass={states:{...fixture,'sensor.other':{state:'99'}}};assert.equal(creates,2);
 console.log('Graph lifecycle checks passed: unrelated updates skipped, pending helpers shared, graph stays mounted and explanation state preserved.');
})().catch(error=>{console.error(error);process.exitCode=1;});

const compact=new Card();compact.setConfig({entity:'sensor.radon_monitor_concentration',show_graph:false});
const healthy={...states,'sensor.radon_monitor_status':{state:'normal',attributes:{weekly_trend:{direction:'falling',change:-2.5}}}};
for(const key of ['sustained_elevated_radon','sustained_high_radon','sensor_problem'])healthy['binary_sensor.radon_monitor_'+key]={state:'off',attributes:{}};
healthy['sensor.radon_monitor_7_days_average']={state:'27.87',attributes:{bucket_coverage_percent:99.68,partial:false}};
compact.hass={states:healthy};assert.match(compact.shadowRoot.innerHTML,/All checks OK/);assert.doesNotMatch(compact.shadowRoot.innerHTML,/99.7% hourly coverage/);assert.match(compact.shadowRoot.innerHTML,/Falling/);
healthy['binary_sensor.radon_monitor_sensor_problem'].state='unavailable';compact.hass={states:healthy};assert.doesNotMatch(compact.shadowRoot.innerHTML,/All checks OK/);assert.match(compact.shadowRoot.innerHTML,/>Unknown</);
compact.setConfig({entity:'sensor.radon_monitor_concentration',show_graph:false,averages:['1_year'],show_trend:false});assert.doesNotMatch(compact.shadowRoot.innerHTML,/>7 days</);assert.match(compact.shadowRoot.innerHTML,/>1 year</);assert.doesNotMatch(compact.shadowRoot.innerHTML,/Falling/);
compact.setConfig({entity:'sensor.radon_monitor_concentration',show_graph:false,averages:[]});assert.doesNotMatch(compact.shadowRoot.innerHTML,/Rolling averages ·/);
editor.form.listeners['value-changed']({detail:{value:{...editor.form.data,days_to_show:'730',show_info:false,averages:['1_year']}}});assert.equal(editor.event.detail.config.days_to_show,730);assert.equal(editor.event.detail.config.show_info,false);assert.equal(editor.event.detail.config.averages[0],'1_year');assert.equal(editor.event.type,'config-changed');
console.log('Visual editor and compact display checks passed.');

const quiet=new Card();quiet.setConfig({entity:'sensor.quiet_concentration',show_graph:false});let renders=0;quiet.render=()=>{renders++;};
quiet.hass={states:{'sensor.quiet_concentration':{state:'40',attributes:{source:'sensor.source'},last_updated:'a'},'sensor.quiet_status':{state:'normal',attributes:{source_age_seconds:1}},'sensor.source':{state:'40',attributes:{}}}};
quiet.hass={states:{'sensor.quiet_concentration':{state:'40',attributes:{source:'sensor.source'},last_updated:'b'},'sensor.quiet_status':{state:'normal',attributes:{source_age_seconds:2}},'sensor.source':{state:'41',attributes:{}}}};assert.equal(renders,1);
quiet.hass={states:{'sensor.quiet_concentration':{state:'41',attributes:{source:'sensor.source'}},'sensor.quiet_status':{state:'normal',attributes:{source_age_seconds:3}}}};assert.equal(renders,2);assert.equal(quiet.getGridOptions().rows,'auto');
const formData=editor.form.data;editor.hass={states:{}};assert.equal(editor.form.data,formData);
console.log('Timestamp filtering, graph throttling, repeated config and automatic height checks passed.');
