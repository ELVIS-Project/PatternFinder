var vrvToolkit = new verovio.toolkit();

var kern_boilerplate =
`**kern
*clefG2
*k[]
*M4/4
=-
4c 4e 4a 4cc
4B- f b- dd
`;

var krn_verovio_options = {
    inputFormat: "humdrum",
    adjustPageHeight: 1,
    pageHeight: 1000,
    pageWidth: 1000,
    scale: 40,
    font: "Leipzig"
};

Vue.component("verovio-humdrum-viewer", {
    data: function() {
        return {
            input: kern_boilerplate
        }
    },
    methods: {
        update: function(e) {
            this.input = e.target.value;
        }
    },
    computed: {
        verovioOutput: function() {
            return vrvToolkit.renderData(this.input, krn_verovio_options)
        }
    },
    template: `
    <form name="inputForm" action="/vue/search" method="post">
        <span class="form-group pull-left">
            <input type="text" value="krn" name="inputType"/>
            <textarea name="krnText" class='form-control'
                v-bind:value="input"
                v-on:input="update">
            </textarea>
        </span>
        <span class="pull-left"
            v-html="verovioOutput"> {{input}}{{verovioOutput}}
        </span>
        <input type="submit" value="Search!">
    </form>`
});

var xml_verovio_options = {
    inputFormat: "xml",
    scale: 40,
    font: "Leipzig"
};

Vue.component("result", {
    data: function() {
        return {
            xml: 'init_xml'
        }
    },
    methods: {
        getExcerpt: function(resultid, mass, note_list){
            var res = $.get('/vue/excerpt/' + mass +'/' + note_list.join(',')).done(function(res){
                console.log(res)
                sr = new XMLSerializer()
                xml = sr.serializeToString(res.documentElement)
                svg = vrvToolkit.renderData(xml, xml_verovio_options)
                $("#" + resultid).html(svg);
            });
        }
    },
    created: function() {
        this.getExcerpt(this.resultid, this.mass, this.note_list)
    },
    props: ['resultid', 'mass', 'note_list'], 
    template: `
        <div>
            <span v-bind:id="resultid"></span>
        </div>`
});

var vm = new Vue({
    el: "#vueapp",
    methods: {
        getExcerpt: function(mass, note_list){
            var res = $.get('/vue/excerpt/' + mass +'/' + note_list.join(',')).done(function(){
            console.log(res)
            console.log(res.responseText)
            });
        },
        maxWindow: function(notes){
            max = 0
            for (i = 1; i < notes.length; i++){
                cur = notes[i] - notes[i - 1]
                if (cur > max){
                    max = cur
                }
            }
            return max
        }
    },
    computed: {
        response: function(){
            return JSON.parse($('#response').html());
        }
    },
    template: `
        <div>
            <verovio-humdrum-viewer></verovio-humdrum-viewer>
            <div v-for="occs, mass in response">
                <div v-for="(occ, index) in occs">
                    <result v-if="maxWindow(occ) == 1" v-bind:resultid="mass + '_' + index" v-bind:mass="mass" v-bind:note_list="occ"></result>
                </div>
            </div>
        </div>
        `
});
