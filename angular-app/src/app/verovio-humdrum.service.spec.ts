import { TestBed } from '@angular/core/testing';

import { VerovioHumdrumService } from './verovio.service';

describe('VerovioHumdrumService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: VerovioHumdrumService = TestBed.get(VerovioHumdrumService);
    expect(service).toBeTruthy();
  });
});
