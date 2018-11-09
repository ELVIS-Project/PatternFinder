import { TestBed } from '@angular/core/testing';

import { ResultsManagerService } from './results-manager.service';

describe('ResultsManagerService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ResultsManagerService = TestBed.get(ResultsManagerService);
    expect(service).toBeTruthy();
  });
});
