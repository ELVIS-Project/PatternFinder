import { Injectable } from '@angular/core';
import { DefaultService } from 'api/api/default.service';
import { Occurrence } from 'api/model/models';

@Injectable({
  providedIn: 'root'
})
export class ResultsManagerService {

  private results: Occurrence[];

  constructor(private service: DefaultService) { }

  /*
  search(inputType: string, musicQuery: string) {
      service.search(inputType, musicQuery).subscribe((results) => {
  }
  */
}
