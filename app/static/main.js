var vrvToolkit = new verovio.toolkit();

var kern_boilerplate =
`**kern
*clefG2
*k[]
*M4/4
=-
4G
4B
4D`;

var verovio_options = {
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
            console.log(this.input);
            return vrvToolkit.renderData(this.input, verovio_options)
        }
    },
    template: `
    <form>
        <span class="form-group pull-left">
            <textarea class='form-control'
                v-bind:value="input"
                v-on:input="update">
            </textarea>
        </span>
        <span class="pull-left"
            v-html="verovioOutput"> {{input}}{{verovioOutput}}
        </span>
    </form>`
});

var vm = new Vue({
    el: "#vueapp",
});
