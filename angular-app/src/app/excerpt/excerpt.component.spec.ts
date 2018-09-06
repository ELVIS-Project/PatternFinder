import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExcerptComponent } from './excerpt.component';

describe('ExcerptComponent', () => {
  let component: ExcerptComponent;
  let fixture: ComponentFixture<ExcerptComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExcerptComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExcerptComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
