import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { AceEditorModule } from 'ng2-ace-editor';
import { ApiModule } from 'api.module';
import { BASE_PATH } from 'api/variables';

import { AppComponent } from './app.component';
import { ExcerptComponent } from './excerpt/excerpt.component';
import { MusicEditorComponent } from './music-editor/music-editor.component';

@NgModule({
  declarations: [
    AppComponent,
    ExcerptComponent,
    MusicEditorComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    NgbModule,
    AceEditorModule,
    ApiModule
  ],
  providers: [
    {
      provide: BASE_PATH,
      useValue: "http://132.206.14.238:80"
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
