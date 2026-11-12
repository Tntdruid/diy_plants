/*! For license information please see diy-plants-card.js.LICENSE.txt */
(()=>{"use strict";const e=globalThis,t=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),i=new WeakMap;class r{constructor(e,t,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const s=this.t;if(t&&void 0===e){const t=void 0!==s&&1===s.length;t&&(e=i.get(s)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&i.set(s,e))}return e}toString(){return this.cssText}}const n=(s,i)=>{if(t)s.adoptedStyleSheets=i.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const t of i){const i=document.createElement("style"),r=e.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=t.cssText,s.appendChild(i)}},o=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const s of e.cssRules)t+=s.cssText;return(e=>new r("string"==typeof e?e:e+"",void 0,s))(t)})(e):e,{is:a,defineProperty:l,getOwnPropertyDescriptor:c,getOwnPropertyNames:h,getOwnPropertySymbols:d,getPrototypeOf:u}=Object,m=globalThis,p=m.trustedTypes,g=p?p.emptyScript:"",f=m.reactiveElementPolyfillSupport,v=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?g:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let s=e;switch(t){case Boolean:s=null!==e;break;case Number:s=null===e?null:Number(e);break;case Object:case Array:try{s=JSON.parse(e)}catch(e){s=null}}return s}},_=(e,t)=>!a(e,t),$={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:_};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;class y extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=$){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(e,s,t);void 0!==i&&l(this.prototype,e,i)}}static getPropertyDescriptor(e,t,s){const{get:i,set:r}=c(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:i,set(t){const n=i?.call(this);r?.call(this,t),this.requestUpdate(e,n,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??$}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const e=u(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const e=this.properties,t=[...h(e),...d(e)];for(const s of t)this.createProperty(s,e[s])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,s]of t)this.elementProperties.set(e,s)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const s=this._$Eu(e,t);void 0!==s&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const s=new Set(e.flat(1/0).reverse());for(const e of s)t.unshift(o(e))}else void 0!==e&&t.push(o(e));return t}static _$Eu(e,t){const s=t.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return n(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){const s=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,s);if(void 0!==i&&!0===s.reflect){const r=(void 0!==s.converter?.toAttribute?s.converter:b).toAttribute(t,s.type);this._$Em=e,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(e,t){const s=this.constructor,i=s._$Eh.get(e);if(void 0!==i&&this._$Em!==i){const e=s.getPropertyOptions(i),r="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:b;this._$Em=i;const n=r.fromAttribute(t,e.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(e,t,s,i=!1,r){if(void 0!==e){const n=this.constructor;if(!1===i&&(r=this[e]),s??=n.getPropertyOptions(e),!((s.hasChanged??_)(r,t)||s.useDefault&&s.reflect&&r===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,s))))return;this.C(e,t,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:i,wrapped:r},n){s&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==r||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),!0===i&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,s]of e){const{wrapped:e}=s,i=this[t];!0!==e||this._$AL.has(t)||void 0===i||this.C(t,void 0,s,i)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}}y.elementStyles=[],y.shadowRootOptions={mode:"open"},y[v("elementProperties")]=new Map,y[v("finalized")]=new Map,f?.({ReactiveElement:y}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,w=e=>e,A=x.trustedTypes,S=A?A.createPolicy("lit-html",{createHTML:e=>e}):void 0,E="$lit$",M=`lit$${Math.random().toFixed(9).slice(2)}$`,C="?"+M,k=`<${C}>`,P=document,U=()=>P.createComment(""),N=e=>null===e||"object"!=typeof e&&"function"!=typeof e,O=Array.isArray,z="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,T=/-->/g,R=/>/g,D=RegExp(`>|${z}(?:([^\\s"'>=/]+)(${z}*=${z}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),I=/'/g,L=/"/g,j=/^(?:script|style|textarea|title)$/i,B=e=>(t,...s)=>({_$litType$:e,strings:t,values:s}),F=B(1),V=(B(2),B(3),Symbol.for("lit-noChange")),W=Symbol.for("lit-nothing"),q=new WeakMap,Y=P.createTreeWalker(P,129);function J(e,t){if(!O(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==S?S.createHTML(t):t}const K=(e,t)=>{const s=e.length-1,i=[];let r,n=2===t?"<svg>":3===t?"<math>":"",o=H;for(let t=0;t<s;t++){const s=e[t];let a,l,c=-1,h=0;for(;h<s.length&&(o.lastIndex=h,l=o.exec(s),null!==l);)h=o.lastIndex,o===H?"!--"===l[1]?o=T:void 0!==l[1]?o=R:void 0!==l[2]?(j.test(l[2])&&(r=RegExp("</"+l[2],"g")),o=D):void 0!==l[3]&&(o=D):o===D?">"===l[0]?(o=r??H,c=-1):void 0===l[1]?c=-2:(c=o.lastIndex-l[2].length,a=l[1],o=void 0===l[3]?D:'"'===l[3]?L:I):o===L||o===I?o=D:o===T||o===R?o=H:(o=D,r=void 0);const d=o===D&&e[t+1].startsWith("/>")?" ":"";n+=o===H?s+k:c>=0?(i.push(a),s.slice(0,c)+E+s.slice(c)+M+d):s+M+(-2===c?t:d)}return[J(e,n+(e[s]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),i]};class Z{constructor({strings:e,_$litType$:t},s){let i;this.parts=[];let r=0,n=0;const o=e.length-1,a=this.parts,[l,c]=K(e,t);if(this.el=Z.createElement(l,s),Y.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(i=Y.nextNode())&&a.length<o;){if(1===i.nodeType){if(i.hasAttributes())for(const e of i.getAttributeNames())if(e.endsWith(E)){const t=c[n++],s=i.getAttribute(e).split(M),o=/([.?@])?(.*)/.exec(t);a.push({type:1,index:r,name:o[2],strings:s,ctor:"."===o[1]?te:"?"===o[1]?se:"@"===o[1]?ie:ee}),i.removeAttribute(e)}else e.startsWith(M)&&(a.push({type:6,index:r}),i.removeAttribute(e));if(j.test(i.tagName)){const e=i.textContent.split(M),t=e.length-1;if(t>0){i.textContent=A?A.emptyScript:"";for(let s=0;s<t;s++)i.append(e[s],U()),Y.nextNode(),a.push({type:2,index:++r});i.append(e[t],U())}}}else if(8===i.nodeType)if(i.data===C)a.push({type:2,index:r});else{let e=-1;for(;-1!==(e=i.data.indexOf(M,e+1));)a.push({type:7,index:r}),e+=M.length-1}r++}}static createElement(e,t){const s=P.createElement("template");return s.innerHTML=e,s}}function G(e,t,s=e,i){if(t===V)return t;let r=void 0!==i?s._$Co?.[i]:s._$Cl;const n=N(t)?void 0:t._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(e),r._$AT(e,s,i)),void 0!==i?(s._$Co??=[])[i]=r:s._$Cl=r),void 0!==r&&(t=G(e,r._$AS(e,t.values),r,i)),t}class Q{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:s}=this._$AD,i=(e?.creationScope??P).importNode(t,!0);Y.currentNode=i;let r=Y.nextNode(),n=0,o=0,a=s[0];for(;void 0!==a;){if(n===a.index){let t;2===a.type?t=new X(r,r.nextSibling,this,e):1===a.type?t=new a.ctor(r,a.name,a.strings,this,e):6===a.type&&(t=new re(r,this,e)),this._$AV.push(t),a=s[++o]}n!==a?.index&&(r=Y.nextNode(),n++)}return Y.currentNode=P,i}p(e){let t=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}}class X{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,s,i){this.type=2,this._$AH=W,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=G(this,e,t),N(e)?e===W||null==e||""===e?(this._$AH!==W&&this._$AR(),this._$AH=W):e!==this._$AH&&e!==V&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>O(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==W&&N(this._$AH)?this._$AA.nextSibling.data=e:this.T(P.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:s}=e,i="number"==typeof s?this._$AC(e):(void 0===s.el&&(s.el=Z.createElement(J(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(t);else{const e=new Q(i,this),s=e.u(this.options);e.p(t),this.T(s),this._$AH=e}}_$AC(e){let t=q.get(e.strings);return void 0===t&&q.set(e.strings,t=new Z(e)),t}k(e){O(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let s,i=0;for(const r of e)i===t.length?t.push(s=new X(this.O(U()),this.O(U()),this,this.options)):s=t[i],s._$AI(r),i++;i<t.length&&(this._$AR(s&&s._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=w(e).nextSibling;w(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class ee{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,i,r){this.type=1,this._$AH=W,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=r,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=W}_$AI(e,t=this,s,i){const r=this.strings;let n=!1;if(void 0===r)e=G(this,e,t,0),n=!N(e)||e!==this._$AH&&e!==V,n&&(this._$AH=e);else{const i=e;let o,a;for(e=r[0],o=0;o<r.length-1;o++)a=G(this,i[s+o],t,o),a===V&&(a=this._$AH[o]),n||=!N(a)||a!==this._$AH[o],a===W?e=W:e!==W&&(e+=(a??"")+r[o+1]),this._$AH[o]=a}n&&!i&&this.j(e)}j(e){e===W?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class te extends ee{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===W?void 0:e}}class se extends ee{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==W)}}class ie extends ee{constructor(e,t,s,i,r){super(e,t,s,i,r),this.type=5}_$AI(e,t=this){if((e=G(this,e,t,0)??W)===V)return;const s=this._$AH,i=e===W&&s!==W||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,r=e!==W&&(s===W||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class re{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){G(this,e)}}const ne=x.litHtmlPolyfillSupport;ne?.(Z,X),(x.litHtmlVersions??=[]).push("3.3.3");const oe=globalThis;class ae extends y{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,s)=>{const i=s?.renderBefore??t;let r=i._$litPart$;if(void 0===r){const e=s?.renderBefore??null;i._$litPart$=r=new X(t.insertBefore(U(),e),e,void 0,s??{})}return r._$AI(e),r})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return V}}ae._$litElement$=!0,ae.finalized=!0,oe.litElementHydrateSupport?.({LitElement:ae});const le=oe.litElementPolyfillSupport;le?.({LitElement:ae}),(oe.litElementVersions??=[]).push("4.2.2");const ce={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:_},he=(e=ce,t,s)=>{const{kind:i,metadata:r}=s;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===i&&((e=Object.create(e)).wrapped=!0),n.set(s.name,e),"accessor"===i){const{name:i}=s;return{set(s){const r=t.get.call(this);t.set.call(this,s),this.requestUpdate(i,r,e,!0,s)},init(t){return void 0!==t&&this.C(i,void 0,e,t),t}}}if("setter"===i){const{name:i}=s;return function(s){const r=this[i];t.call(this,s),this.requestUpdate(i,r,e,!0,s)}}throw Error("Unsupported decorator location: "+i)};function de(e){return(t,s)=>"object"==typeof s?he(e,t,s):((e,t,s)=>{const i=t.hasOwnProperty(s);return t.constructor.createProperty(s,e),i?Object.getOwnPropertyDescriptor(t,s):void 0})(e,t,s)}var ue,me;!function(e){e.language="language",e.system="system",e.comma_decimal="comma_decimal",e.decimal_comma="decimal_comma",e.space_comma="space_comma",e.none="none"}(ue||(ue={})),function(e){e.language="language",e.system="system",e.am_pm="12",e.twenty_four="24"}(me||(me={})),new Set(["fan","input_boolean","light","switch","group","automation"]);new Set(["call-service","divider","section","weblink","cast","select"]);const pe=((e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,s,i)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+e[i+1],e[0]);return new r(i,e,s)})`
  :host {
    display: block;
  }

  ha-card {
    overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 10%, transparent);
    background: linear-gradient(145deg, color-mix(in srgb, #6c9a72 8%, var(--card-background-color)), var(--card-background-color));
  }

  .header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    min-height: 76px;
    padding: 14px 16px;
    border-bottom: 1px solid color-mix(in srgb, var(--primary-text-color) 9%, transparent);
    background: linear-gradient(100deg, color-mix(in srgb, #6c9a72 14%, transparent), transparent 58%);
    cursor: pointer;
  }

  .header-icon {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 50%;
    color: #47734e;
    background: color-mix(in srgb, #6c9a72 20%, var(--card-background-color));
    box-shadow: inset 0 0 0 1px color-mix(in srgb, #6c9a72 28%, transparent);
  }

  .plant-image {
    flex: 0 0 50px;
    width: 50px;
    height: 50px;
    border: 3px solid color-mix(in srgb, var(--primary-color) 34%, var(--card-background-color));
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  }

  .heading {
    min-width: 0;
    flex: 1 1 160px;
  }

  ha-card.text-size-small { --card-text-scale: 0.92; }
  ha-card.text-size-medium { --card-text-scale: 1; }
  ha-card.text-size-large { --card-text-scale: 1.12; }

  .name {
    overflow: hidden;
    color: var(--primary-text-color);
    font-size: calc(1.16rem * var(--card-text-scale, 1));
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .subtitle {
    margin-top: 3px;
    color: var(--secondary-text-color);
    font-size: calc(0.86rem * var(--card-text-scale, 1));
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .health {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 5px;
    padding: 5px 8px;
    border: 1px solid color-mix(in srgb, currentColor 22%, transparent);
    border-radius: 999px;
    background: color-mix(in srgb, currentColor 8%, transparent);
    color: var(--secondary-text-color);
    font-size: calc(0.88rem * var(--card-text-scale, 1));
  }

  .health.good { color: var(--success-color, #43a047); }
  .health.bad { color: var(--error-color, #db4437); }
  .health.unavailable { color: var(--disabled-text-color); }

  .measurements {
    display: grid;
    grid-template-columns: repeat(var(--bars-per-row), minmax(0, 1fr));
    gap: 2px;
    padding: 8px;
  }

  .measurement {
    min-width: 0;
    margin: 3px;
    padding: 11px 10px 9px;
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 8%, transparent);
    border-radius: 8px;
    background: color-mix(in srgb, var(--card-background-color) 86%, var(--primary-background-color));
  }

  .measurement.clickable {
    cursor: pointer;
  }

  .measurement.clickable:hover,
  .measurement.clickable:focus-visible {
    border-color: color-mix(in srgb, var(--primary-color) 45%, transparent);
    outline: none;
  }

  .measurement-heading,
  .value-line {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .measurement-heading {
    color: var(--secondary-text-color);
    font-size: calc(0.9rem * var(--card-text-scale, 1));
  }

  .measurement-heading ha-icon {
    color: #5f9168;
    --mdc-icon-size: 19px;
  }

  .measurement-heading span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .value-line {
    justify-content: space-between;
    margin-top: 8px;
  }

  .value {
    color: var(--primary-text-color);
    font-size: calc(1.1rem * var(--card-text-scale, 1));
    font-weight: 600;
  }

  .unit {
    color: var(--secondary-text-color);
    font-size: calc(0.84rem * var(--card-text-scale, 1));
    font-weight: 400;
  }

  .value-line > ha-icon {
    --mdc-icon-size: 18px;
  }

  .value-line > ha-icon.good { color: var(--success-color, #43a047); }
  .value-line > ha-icon.bad { color: var(--error-color, #db4437); }
  .value-line > ha-icon.unavailable { color: var(--disabled-text-color); }

  .meter {
    height: 7px;
    margin-top: 8px;
    overflow: hidden;
    border-radius: 3px;
    background: color-mix(in srgb, var(--divider-color) 72%, transparent);
  }

  .meter-fill {
    height: 100%;
    border-radius: inherit;
    transition: width 220ms ease;
  }

  .meter-fill.good { background: var(--success-color, #43a047); }
  .meter-fill.bad { background: var(--error-color, #db4437); }
  .meter-fill.unavailable { background: var(--disabled-text-color); }

  .range {
    display: flex;
    justify-content: space-between;
    margin-top: 5px;
    color: var(--secondary-text-color);
    font-size: calc(0.76rem * var(--card-text-scale, 1));
    opacity: 0.82;
  }

  .range b {
    margin-right: 2px;
    color: var(--primary-text-color);
    font-weight: 500;
  }

  .warning {
    padding: 16px;
    color: var(--secondary-text-color);
  }

  @media (max-width: 420px) {
    .measurements { grid-template-columns: 1fr; }
  }

  @media (max-width: 600px) {
    ha-card.text-size-small { --card-text-scale: 0.86; }
    ha-card.text-size-medium { --card-text-scale: 0.92; }
    ha-card.text-size-large { --card-text-scale: 1.02; }

    .header {
      gap: 9px;
      padding: 12px;
    }

    .heading {
      flex-basis: 100%;
    }

    .name {
      white-space: normal;
      overflow-wrap: anywhere;
    }

    .measurement {
      margin: 2px;
      padding: 9px 8px 8px;
    }

    .measurements {
      gap: 1px;
      padding: 6px;
    }
  }
`,ge=["moisture","conductivity","temperature","air_temperature","humidity","illuminance","dli"],fe={moisture:"Soil moisture",conductivity:"Soil conductivity",temperature:"Soil temperature",air_temperature:"Air temperature",humidity:"Air humidity",illuminance:"Illuminance",dli:"DLI"},ve={moisture:"mdi:water-percent",conductivity:"mdi:leaf",temperature:"mdi:thermometer",air_temperature:"mdi:thermometer-lines",humidity:"mdi:water-percent",illuminance:"mdi:brightness-5",dli:"mdi:weather-sunny"};function be(e,t){return"number"==typeof t&&Number.isFinite(t)?"moisture"===e||"humidity"===e?String(Math.round(t)):function(e){return"number"==typeof e&&Number.isFinite(e)?Number.isInteger(e)?String(e):e.toFixed(1).replace(/\.0$/,""):"Unavailable"}(t):"Unavailable"}const _e={en:{measurements:"Measurements",appearance:"Appearance",entity:"Entity",name:"Display name",image:"Plant photo URL",showMeasurements:"Measurements to show",moistureMin:"Minimum soil moisture",moistureMax:"Maximum soil moisture",moistureMinSensor:"Minimum moisture sensor",moistureMaxSensor:"Maximum moisture sensor",fertilizerSensor:"Fertilizer reminder sensor",minimum:"Min",maximum:"Max",displayType:"Display type",textSize:"Text size",small:"Small",normal:"Normal",large:"Large",full:"Full",compact:"Compact",showHealth:"Show health status",hideUnits:"Hide units",barsPerRow:"Bars per row",subtitle:"DIY Plants",unavailableEntity:"Entity not available",noMeasurements:"No DIY Plants measurements are available.",statusOk:"OK",statusAttention:"Attention",statusUnavailable:"Unavailable",statusNoSensors:"No sensors",statusStale:"Sensor not updating",metrics:fe},da:{measurements:"Målinger",appearance:"Udseende",entity:"Entitet",name:"Visningsnavn",image:"URL til plantefoto",showMeasurements:"Målinger der vises",moistureMin:"Minimum jordfugtighed",moistureMax:"Maksimum jordfugtighed",moistureMinSensor:"Sensor for minimum jordfugtighed",moistureMaxSensor:"Sensor for maksimum jordfugtighed",fertilizerSensor:"Gødningssensor",minimum:"Min",maximum:"Maks",displayType:"Visningstype",textSize:"Tekststørrelse",small:"Lille",normal:"Normal",large:"Stor",full:"Fuld",compact:"Kompakt",showHealth:"Vis sundhedsstatus",hideUnits:"Skjul enheder",barsPerRow:"Målinger pr. række",subtitle:"DIY Plants",unavailableEntity:"Entiteten er ikke tilgængelig",noMeasurements:"Ingen DIY Plants-målinger er tilgængelige.",statusOk:"OK",statusAttention:"Bemærk",statusUnavailable:"Ikke tilgængelig",statusNoSensors:"Ingen sensorer",statusStale:"Sensor opdaterer ikke",metrics:{moisture:"Jordfugtighed",conductivity:"Jordens ledningsevne",temperature:"Jordtemperatur",air_temperature:"Lufttemperatur",humidity:"Luftfugtighed",illuminance:"Belysning",dli:"DLI"}}};function $e(e){const t=e?.locale?.language??("undefined"!=typeof document?document.documentElement.lang:"");return t?.toLowerCase().startsWith("da")?"da":"en"}function ye(e){return _e[e]}function xe(e,t){return ye(t).metrics[e]??e.replaceAll("_"," ")}function we(e,t){const s=e.toLowerCase(),i=ye(t);return s.includes("unavailable")?i.statusUnavailable:s.includes("stale")?i.statusStale:"no_sensors"===s||"no sensors"===s?i.statusNoSensors:s.includes("attention")?i.statusAttention:s.includes("ok")?i.statusOk:e}var Ae=function(e,t,s,i){var r,n=arguments.length,o=n<3?t:null===i?i=Object.getOwnPropertyDescriptor(t,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(e,t,s,i);else for(var a=e.length-1;a>=0;a--)(r=e[a])&&(o=(n<3?r(o):n>3?r(t,s,o):r(t,s))||o);return n>3&&o&&Object.defineProperty(t,s,o),o};const Se="diy-plants-card",Ee=e=>F`<ha-icon .icon=${e}></ha-icon>`;class Me extends ae{hass;config;setConfig(e){if(!e.entity)throw new Error("You need to define the DIY Plants health entity");this.config=e}getCardSize(){return 3}static getStubConfig(){return{type:`custom:${Se}`,entity:"sensor.my_plant_health"}}static getConfigForm(){const e="undefined"!=typeof document&&document.documentElement.lang.toLowerCase().startsWith("da")?"da":"en",t=ye(e);return{schema:[{name:"entity",required:!0,selector:{entity:{domain:"sensor"}}},{name:"name",selector:{text:{}}},{name:"subtitle",selector:{text:{}}},{name:"image",selector:{text:{}}},{name:"fertilizer_sensor",selector:{entity:{domain:"sensor"}}},{type:"expandable",name:"",title:t.measurements,schema:[{name:"show_measurements",selector:{select:{multiple:!0,options:Object.keys(fe).map(t=>({value:t,label:xe(t,e)}))}}},{name:"moisture_min",selector:{number:{min:0,max:100,step:1,mode:"box"}}},{name:"moisture_max",selector:{number:{min:0,max:100,step:1,mode:"box"}}},{name:"moisture_min_sensor",selector:{entity:{domain:"sensor"}}},{name:"moisture_max_sensor",selector:{entity:{domain:"sensor"}}}]},{type:"expandable",name:"",title:t.appearance,schema:[{name:"display_type",selector:{select:{options:[{value:"full",label:t.full},{value:"compact",label:t.compact}]}}},{name:"show_health",selector:{boolean:{}}},{name:"text_size",selector:{select:{options:[{value:"small",label:t.small},{value:"medium",label:t.normal},{value:"large",label:t.large}]}}},{name:"hide_units",selector:{boolean:{}}},{name:"bars_per_row",selector:{number:{min:1,max:2,step:1,mode:"box"}}}]}],computeLabel:e=>({entity:t.entity,name:t.name,subtitle:t.subtitle,image:t.image,fertilizer_sensor:t.fertilizerSensor,show_measurements:t.showMeasurements,moisture_min:t.moistureMin,moisture_max:t.moistureMax,moisture_min_sensor:t.moistureMinSensor,moisture_max_sensor:t.moistureMaxSensor,display_type:t.displayType,text_size:t.textSize,show_health:t.showHealth,hide_units:t.hideUnits,bars_per_row:t.barsPerRow}[e.name]??e.name)}}openMoreInfo(e=this.config?.entity){e&&((e,t,s,i)=>{i=i||{},s=s??{};const r=new Event(t,{bubbles:void 0===i.bubbles||i.bubbles,cancelable:Boolean(i.cancelable),composed:void 0===i.composed||i.composed});r.detail=s,e.dispatchEvent(r)})(this,"hass-more-info",{entityId:e})}renderMeasurement(e,t){const s=$e(this.hass),i=this.config?.moisture_min_sensor?this.hass?.states[this.config.moisture_min_sensor]:void 0,r=this.config?.moisture_max_sensor?this.hass?.states[this.config.moisture_max_sensor]:void 0,n=i?Number(String(i.state).replace(",",".")):Number.NaN,o=r?Number(String(r.state).replace(",",".")):Number.NaN,a="moisture"===e?{...t,minimum:Number.isFinite(n)?n:this.config?.moisture_min??t.minimum,maximum:Number.isFinite(o)?o:this.config?.moisture_max??t.maximum}:t,l=function(e){return"unavailable"!==e.status&&"stale"!==e.status&&"number"==typeof e.value&&Number.isFinite(e.value)?"low"===e.status||"high"===e.status?"bad":"good":"unavailable"}(a),c=function(e){if("number"!=typeof e.value||!Number.isFinite(e.value))return null;if("number"!=typeof e.minimum||"number"!=typeof e.maximum)return null;if(e.minimum===e.maximum)return 100;const t=(e.value-e.minimum)/(e.maximum-e.minimum)*100;return Math.max(0,Math.min(100,t))}(a)??0,h=this.config?.hide_units??"compact"===this.config?.display_type?"":t.unit??"",d=xe(e,s),u=ve[e]??"mdi:sprout",m=this.config?.measurement_entities?.[e]??a.entity_id??a.source_entity;return F`
      <div
        class="measurement${m?" clickable":""}"
        title=${m?`${d}: ${m}`:d}
        role=${m?"button":"presentation"}
        tabindex=${m?"0":"-1"}
        @click=${m?()=>this.openMoreInfo(m):void 0}
        @keydown=${m?e=>{"Enter"!==e.key&&" "!==e.key||(e.preventDefault(),this.openMoreInfo(m))}:void 0}
      >
        <div class="measurement-heading">${Ee(u)}<span>${d}</span></div>
        <div class="value-line">
          <span class="value">${be(e,a.value)} <span class="unit">${h}</span></span>
          <ha-icon class="${l}" .icon=${"bad"===l?"mdi:alert-circle-outline":"unavailable"===l?"mdi:help-circle-outline":"mdi:check-circle-outline"}></ha-icon>
        </div>
        <div class="meter"><div class="meter-fill ${l}" style="width: ${c}%"></div></div>
        ${"number"==typeof a.minimum&&"number"==typeof a.maximum?F`<div class="range"><span><b>${ye(s).minimum}</b> ${be(e,a.minimum)}${h}</span><span><b>${ye(s).maximum}</b> ${be(e,a.maximum)}${h}</span></div>`:""}
      </div>
    `}render(){if(!this.config||!this.hass)return F``;const e=$e(this.hass),t=ye(e),s=this.hass.states[this.config.entity??""];if(!s)return F`<ha-card><div class="warning">${t.unavailableEntity}: ${this.config.entity}</div></ha-card>`;const i=function(e){const t=e?.attributes.measurements;return!t||"object"!=typeof t||Array.isArray(t)?{}:t}(s),r=(this.config.show_measurements??ge).filter(e=>i[e]),n=this.config.name??String(s.attributes.friendly_name??s.entity_id),o=this.config.subtitle??t.subtitle,a=this.config.image??("string"==typeof s.attributes.entity_picture?s.attributes.entity_picture:void 0),l=this.config.show_health??!0,c=s.state.toLowerCase().includes("ok")?"good":/unavailable|stale/.test(s.state.toLowerCase())?"unavailable":"bad",h=this.config.fertilizer_sensor?this.hass.states[this.config.fertilizer_sensor]:void 0,d=h?h.state.toLowerCase().includes("ok")?"good":h.state.toLowerCase().includes("unavailable")?"unavailable":"bad":"unavailable",u=this.config.bars_per_row??("compact"===this.config.display_type?1:2),m=this.config.text_size??"medium";return F`
      <ha-card class="text-size-${m}">
        <div class="header" @click=${()=>this.openMoreInfo()}>
          ${a?F`<img class="plant-image" src=${a} alt=${n}>`:F`<div class="header-icon">${Ee("mdi:flower")}</div>`}
          <div class="heading">
            <div class="name">${n}</div>
            <div class="subtitle">${o}</div>
            </div>
            ${l?F`<div class="health ${c}">${Ee("good"===c?"mdi:heart-pulse":"mdi:alert-circle-outline")}<span>${we(s.state,e)}</span></div>`:""}
            ${h&&"good"!==d?F`<div class="health ${d}">${Ee("mdi:leaf")}<span>${we(h.state,e)}</span></div>`:""}
        </div>
        ${r.length>0?F`<div class="measurements" style="--bars-per-row: ${u}">${r.map(e=>this.renderMeasurement(e,i[e]))}</div>`:F`<div class="warning">${t.noMeasurements}</div>`}
      </ha-card>
    `}static get styles(){return pe}}Ae([de({attribute:!1})],Me.prototype,"hass",void 0),Ae([de({attribute:!1})],Me.prototype,"config",void 0),customElements.get(Se)||(customElements.define(Se,Me),window.customCards??=[],window.customCards.push({type:Se,name:"DIY Plants Card",description:"Display measurements from the DIY Plants Home Assistant integration",preview:!0}))})();