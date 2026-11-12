import _ from 'lodash';

export const titleCase = (s) => _.startCase(_.toLower(s));
export const debounce = (fn, ms) => _.debounce(fn, ms);
