import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MusicEditorComponent } from './music-editor.component';

describe('MusicEditorComponent', () => {
  let component: MusicEditorComponent;
  let fixture: ComponentFixture<MusicEditorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MusicEditorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MusicEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
