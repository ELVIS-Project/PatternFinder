/*
require.config({
    paths: {
        jquery: "https://code.jquery.com/jquery-3.3.1.min.js",
        vue: "https://cdn.jsdelivr.net/npm/vue@2.5.16/dist/vue.min.js",
        vrvHumdrum: "http://verovio-script.humdrum.org/scripts/verovio-toolkit.js",
        aceModeHumdrum: "https://verovio.humdrum.org/scripts/ace/mode-humdrum.js",
        aceModeXml: "https://verovio.humdrum.org/scripts/ace/mode-xml.js",
        infiniteScroll: "https://unpkg.com/vue-infinite-scroll",
        ace: "https://cdnjs.cloudflare.com/ajax/libs/ace/1.3.3/ace.js"
    }
});
*/

var vrvToolkit = new verovio.toolkit();

Vue.component("verovio-humdrum-viewer", {
    data: function() {
        return {
            input: document.getElementById('default_krn').text,
            vrv_options: {
                inputFormat: "humdrum",
                adjustPageHeight: 1,
                pageHeight: 1000,
                pageWidth: 1000,
                scale: 60,
                font: "Leipzig"
            }
        }
    },
    methods: {
        update: function(newstr) {
            this.input = newstr
        }
    },
    computed: {
        verovioOutput: function() {
            return vrvToolkit.renderData(this.input, this.vrv_options)
        }
    },
    mounted: function(){
        var onChange = this.update

        var editor = ace.edit("editor", {
            autoScrollEditorIntoView: true,
            maxLines: 10,
            value: this.input
        })
        editor.session.on('change', function(delta){
            onChange(editor.getValue())
        })
    },
    template: `
    <form name="inputForm" action="/vue/search" method="get">
        <div class="container">
            <div class="row">
                <span class="col-md-3"></span>
                <pre class="col-md-3" id="editor"></pre>
                <div class="col-md-3">
                    <span v-html="verovioOutput"></span>
                    <input class="btn btn-primary form-control" type="submit" value="Search!">
                </div>
            </div>
        </div>
    </form>`
});

var vanillaVerovio = document.createElement('script');
vanillaVerovio.setAttribute('src', 'http://www.verovio.org/javascript/latest/verovio-toolkit.js')
document.head.appendChild(vanillaVerovio)

Vue.component("result", {
    data: function() {
        return {
            xml: '',
            svg: '',
            vrvToolkit: new verovio.toolkit(),
            vrv_options: {
                scale: 40,
                font: "Leipzig",
                adjustPageHeight: 1,
                noFooter: 1,
                noHeader: 1
            }
        }
    },
    methods: {
        renderXml: function(newXml){
            this.xml = newXml
            this.svg = this.vrvToolkit.renderData(newXml, this.vrv_options)
        },
        getExcerpt: function(occ){
            var renderXml = this.renderXml
            var res = $.get('/vue/excerpt/' + occ['mass'] +'/' + occ['notes'].join(',')).done(function(res){
                sr = new XMLSerializer()
                xml = sr.serializeToString(res.documentElement)
                renderXml(xml)
            });
            this.occ.loaded = true;
        }
    },
    created: function() {
        this.getExcerpt(this.occ)
    },
    props: ['occ'], 
    template: `
        <div class="panel">
            <div class="panel panel-heading">
                <h5>{{this.occ['mass'].split('_').join(' ')}}</h5>
            </div>
            <div class="panel panel-body" v-html="svg"></div>
        </div>`
});

var vm = new Vue({
    el: "#vueapp",
    data: {
        searchResponse: JSON.parse($('#searchResponse').html()),
        loadedOccs: [],
        infiniteScrollBusy: false
    },
    computed: {
        filteredOccs: function(){
            return this.searchResponse.filter(this.filterOccForAll)
        }
    },
    filters: {
        deleteParentheses: function(string){
            return mass.replace('(','').replace(')','')
        }
    },
    methods: {
        filterOccForAll: function(occ) {
            return this.filterForMaxWindow(occ)
        },
        loadMoreOccs: function(){
            this.infiniteScrollBusy = true;

            setTimeout(() => {
                console.log('Loading more occs!')
                for (var i=0; i < 10; i++){
                    nextOccIndex = this.loadedOccs.length + i
                    if (nextOccIndex > this.filteredOccs.length - 1) {
                        console.log("Nothing more to load")
                        break;
                    }

                    if (!this.filteredOccs[nextOccIndex].loaded){
                        console.log("occ passed the filter: " + this.filteredOccs[nextOccIndex])
                        this.loadedOccs.push(this.filteredOccs[nextOccIndex])
                    }
                }
                this.infiniteScrollBusy = false;
            }, 1000)
        },
        getExcerpt: function(results, mass, note_list){
            var res = $.get('/vue/excerpt/' + mass +'/' + note_list.join(',')).done(function(res){
            sr = new XMLSerializer()
            xml = sr.serializeToString(res.documentElement)
            svg = vrvToolkitVanilla.renderData(xml, xml_verovio_options)
            results.push(svg)
            });
        },
        filterForMaxWindow: function(occ){
            notes = occ['notes']
            max = 0
            for (i = 1; i < notes.length; i++){
                cur = notes[i] - notes[i - 1]
                if (cur > max){
                    max = cur
                }
            }
            return max == 1
        }
    },
    template: `
        <div>
            <verovio-humdrum-viewer></verovio-humdrum-viewer>
            <div v-infinite-scroll="loadMoreOccs" infinite-scroll-disabled="infiniteScrollBusy" infinite-scroll-distance="10">
            <div class="container-fluid">
                <div v-for="(occ, index) in loadedOccs">
                    <div class="col-md-6"> <result v-show="filterOccForAll(occ)" v-bind:occ="occ"></result> </div>
                </div>
            </div>
            </div>
        </div>
        `
});
