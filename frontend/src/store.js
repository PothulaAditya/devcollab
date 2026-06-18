/**
 * Simple reactive store for global state.
 */
const state = {
  user: null,
  loading: false,
};

const listeners = [];

function getState() {
  return state;
}

function setState(updates) {
  Object.assign(state, updates);
  listeners.forEach(fn => fn(state));
}

function subscribe(fn) {
  listeners.push(fn);
  return () => {
    const i = listeners.indexOf(fn);
    if (i > -1) listeners.splice(i, 1);
  };
}

export { getState, setState, subscribe };
