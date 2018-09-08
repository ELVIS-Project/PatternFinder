import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { AceEditorModule } from 'ng2-ace-editor';

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
    NgbModule,
    AceEditorModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
