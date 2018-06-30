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
    props: ['targetWindowFilter', 'transpositionFilter', 'diatonicOccFilter'],
    methods: {
        update: function(newstr) {
            this.input = newstr
        },
        updateProp(eventName, value){
            console.log("update " + eventName + ": ")
            console.log(value)
            this.$emit(eventName, value)
        }
    },
    computed: {
        verovioOutput: function() {
            return vrvToolkit.renderData(this.input, this.vrv_options);
        }
    },
    mounted: function(){
        var onChange = this.update;
        var editorId = "editor";
        var editorDiv = document.getElementById(editorId);

        var editor = ace.edit(editorId, {
            autoScrollEditorIntoView: true,
            value: this.input,
            minLines: 10,
            maxLines: 10
        });
        editor.session.on('change', function(delta){
            onChange(editor.getValue())
        });

        var onPropChange = this.updateProp
        $("#targetWindowSlider").slider({
            range: true,
            min: 1,
            max: 15,
            values: [1, 1],
            slide: function(event, ui){
                onPropChange('targetWindowFilter', ui.values)
            }
        });

        $("#transpositionSlider").slider({
            range: true,
            min: -12,
            max: 12,
            values: [-12, 12],
            slide: function(event, ui){
                onPropChange('transpositionFilter', ui.values)
            }
        });

        $("#diatonicOccFilter").checkboxradio();
    },
    template: `
    <form name="inputForm" action="/vue/search" method="get">
        <input name="krnText" type="hidden" v-model="input"/>
        <input name="inputType" type="hidden" value="krn"/>
        <div class="container-fluid border border-light border-secondary pb-4">
            <div class="row">
                <div class="col-md-4 w-100 pl-0">
                    <pre id="editor"></pre>
                    <input class="btn btn-primary form-control bg-info" type="submit" value="Search!">
                </div>

                <div class="col-md-5 position-relative">
                    <span id="verovioOutput" v-html="verovioOutput"></span>
                    <span class="text-muted" style="position: absolute; bottom: 0; left: 0;">
                        Powered by <a target="_blank" href="https://doc.verovio.humdrum.org">Verovio Humdrum Viewer</a> 
                        and <a target="_blank" href="https://ace.c9.io">Ace text editor</a>
                    </span>
                </div>

                <div class="col-md-3" id="filters">
                    <!-- DIATONIC OCCS -->
                    <label class="w-100 mt-3">
                        <span>Filter out inexact transpositions?</span>
                        <input type="checkbox" class="form-control" v-bind:checked="diatonicOccFilter" id="diatonicOccFilter" v-on:click="updateProp('diatonicOccFilter', $('#diatonicOccFilter').is(':checked'))"/>
                    </label>

                    <!-- TARGET WINDOW -->
                    <span> # of intervening notes</span>
                    <div>
                        <!--
                            Minimum distance between two notes is actually 1,
                            but we refer to it as # of intervening notes
                            So index it from 0 just for the UI
                        -->
                        <span class="mr-2">{{targetWindowFilter[0] - 1}}</span>
                        <div class="w-75 d-inline-block" id="targetWindowSlider"></div>
                        <span class="ml-2">{{targetWindowFilter[1] - 1}}</span>
                    </div>

                    <!-- TRANSPOSITIONS -->
                    <span>Chromatic transpositions mod 12</span>
                    <div>
                        <span class="mr-2">{{transpositionFilter[0]}}</span>
                        <div class="w-75 d-inline-block" id="transpositionSlider"></div>
                        <span class="ml-2">{{transpositionFilter[1]}}</span>
                    </div>
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
            var res = $.get('/vue/excerpt/' + occ['mass'] +'/' + occ['targetNotes'].join(',')).done(function(res){
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
    computed: {
        massProcessed: function() {
            var mass = this.occ['mass'].split('_')
            mass.splice(mass.length - 1, 0, 'à')
            // Ignore the year e.g. (1601)
            return mass.join(' ').replace(/\s\(\.*\)/, '')
        }
    },
    props: ['occ'], 
    template: `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{{massProcessed}}</h5>
            </div>
            <span v-html="svg"></span>
            <!--
            <img v-bind:src="'data:image/svg+xml;charset=utf-8,' + svg">
            -->
        </div>`
});

var vm = new Vue({
    el: "#vueapp",
    data: {
        searchResponse: JSON.parse($('#searchResponse').html()),
        loadedOccs: [],
        infiniteScrollBusy: false,
        transpositionFilter: [-12, 12],
        numNotesFilter: 1,
        diatonicOccFilter: true,
        targetWindowFilter: [1, 1],
        patternWindowFilter: 1
    },
    computed: {
        filteredOccs: function(){
            return this.searchResponse.filter(this.filterOccForAll)
        }
    },
    methods: {
        filterOccForAll: function(occ) {
            //console.log("checking filters on occ ")
            //console.log(occ)
            //console.log("window filter " + this.filterForTargetWindow(occ))
            //console.log("diatonic filter " + this.filterForDiatonicOccs(occ))
            return this.filterForTargetWindow(occ) && this.filterForDiatonicOccs(occ) && this.filterForTransposition(occ)
        },
        loadMoreOccs: function(){
            this.infiniteScrollBusy = true;

            setTimeout(() => {
                console.log('Loading more occs!')
                var numPushed = 0;
                for (occ of this.filteredOccs){
                    if (!occ.loaded){
                        console.log("loading occ: " + occ)
                        this.loadedOccs.push(occ);
                        numPushed++;
                    }
                    if (numPushed > 10){
                        break;
                    }
                }
                /*
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
                */
                this.infiniteScrollBusy = false;
            }, 1000)
        },
        getExcerpt: function(results, mass, note_list){
            var res = $.get('/vue/excerpt/' + mass +'/' + note_list.join(',')).done(function(res){
            sr = new XMLSerializer()
            xml = sr.serializeToString(res.documentElement)
            svg = vrvToolkitVanilla.renderData(xml, xml_verovio_options)
            results.push(svg)
            })
            .fail(function(){
                console.log("Failed to fetch")
            });
        },
        filterForDiatonicOccs: function(occ){
            /* Returns false if the occ is to be filtered out based on being a diatonic occurence*/
            // if the filter's off, take anything
            // otherwise, only take chromatic (flagged as not diatonic) occs
            return (!this.diatonicOccFilter || (!occ['diatonicOcc']))
        },
        filterForTargetWindow: function(occ){
            notes = occ['targetNotes']
            max = 0
            for (i = 1; i < notes.length; i++){
                cur = notes[i] - notes[i - 1]
                if (cur > max){
                    max = cur
                }
            }
            return (max >= this.targetWindowFilter[0]) && (max <= this.targetWindowFilter[1])
        },
        filterForTransposition: function(occ){
            var res = ((occ['transposition'] % 12 >= this.transpositionFilter[0]) && ((occ['transposition'] % 12)  <= this.transpositionFilter[1]))
            if (!res){
                console.log(occ)
                console.log(occ['transposition'] % 12)
                console.log(this.transpositionFilter)
            }
            return res
        }
    },
    template: `
        <div>
            <nav class="navbar navbar-expand-lg navbar-light bg-info">
                <div class="navbar-brand">PatternFinder</div>
                <div class="collapse navbar-collapse"">
                    <ul class="navbar-nav mr-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="about/">About</a>
                        </li>
                        <li class="nav-item">
                            <a target="_blank" class="nav-link" href="https://github.com/ELVIS-Project/PatternFinder">Github</a> 
                        </li>
                    </ul>
                    <span target="_blank" class="nav-text navbar-right">By David Garfinkle</span>
                </div>
            </nav>
  
            <!-- Listen for $emit.('input') event to change values -->
            <verovio-humdrum-viewer
                v-bind:targetWindowFilter="targetWindowFilter"
                v-on:targetWindowFilter="targetWindowFilter = arguments[0]"
                v-bind:diatonicOccFilter="diatonicOccFilter"
                v-on:diatonicOccFilter="diatonicOccFilter = arguments[0]"
                v-bind:transpositionFilter="transpositionFilter"
                v-on:transpositionFilter="transpositionFilter = arguments[0]">
            </verovio-humdrum-viewer>

            <div class="align-middle font-weight-light text-center">#{{filteredOccs.length}} Occurrences</div>
            <div v-init="loadMoreOccs" v-infinite-scroll="loadMoreOccs" infinite-scroll-disabled="infiniteScrollBusy" infinite-scroll-distance="10">
            <div class="container-fluid">
                <div class="row">
                    <div v-for="(occ, index) in loadedOccs" class="col-md-6 pl-0 pr-0"><result v-show="filterOccForAll(occ)" v-bind:occ="occ"></result></div>
                </div>
            </div>
        </div>
        `
});
