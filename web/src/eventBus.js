export class EventBus {
  constructor() {
    this.nextId = 0
    this.listeners = {}
  }

  addListener(eventName, listener) {
    let id = this.nextId++

    if(!this.listeners[eventName]) {
      this.listeners[eventName] = {}
    }

    this.listeners[eventName][id] = listener

    let self = this
    return {
      remove() { delete self.listeners[eventName][id] }
    }
  }

  dispatchEvent(eventName, event) {
    for(let listener of Object.values(this.listeners[eventName] ?? {})) {
      listener(event)
    }
  }
}

export const globalEventBus = new EventBus()
