import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-excerpt',
  templateUrl: './excerpt.component.html',
  styleUrls: ['./excerpt.component.css']
})
export class ExcerptComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}

/*
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
            excerptUrl = '/' + [
                'mass',
                occ['mass'],
                'excerpt',
                occ['targetNotes'].join(',')]
                .join('/')
            var res = $.get(excerptUrl).done(function(res){
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

 */
