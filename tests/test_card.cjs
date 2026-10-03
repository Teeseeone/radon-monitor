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
card.setConfig({entity:'sensor.radon_monitor_concentration',name:'<img onerror="evil">',show_graph:false});
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
const Editor=registry.get('radon-monitor-card-editor');const editor=new Editor();editor.setConfig({entity:'sensor.room_concentration'});editor.hass={states};assert.equal(editor.form.data.entity,'sensor.room_concentration');assert.ok(editor.form.schema.some(s=>s.name==='2_years_average_entity'));
assert.equal(context.window.customCards.length,1);
console.log('Card rendering checks passed: valid/zero/missing values, alerts, partial coverage, escaping, entity overrides, editor and more-info event.');
