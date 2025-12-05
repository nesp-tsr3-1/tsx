import {
  parseParams,
  encodeParams,
  pluck,
  min,
  max,
  uniq,
  pick,
  debounce,
  parseCSV,
  deepEquals,
  throttle,
  searchStringToRegex,
  matchParts,
  capitalise
} from './util.js'

import { expect, test, describe, vi } from 'vitest'

vi.useFakeTimers()

describe('parseParams', () => {
  test('parses single parameter', () => {
    expect(parseParams('a=b')).toEqual({ a: 'b' })
  })

  test('parses two parameters', () => {
    expect(parseParams('a=b&c=d')).toEqual({ a: 'b', c: 'd' })
  })

  test('parses empty string', () => {
    expect(parseParams('')).toEqual({})
  })

  test('parses escaped characters', () => {
    expect(parseParams('a=%3Fx%3Dtest')).toEqual({ a: '?x=test' })
  })
})

describe('encodeParams', () => {
  test('encodes single parameter', () => {
    expect(encodeParams({ a: 'b' })).toBe('a=b')
  })

  test('encodes two parameters', () => {
    expect(encodeParams({ a: 'b', c: 'd' })).toEqual('a=b&c=d')
  })

  test('encodes empty parameters', () => {
    expect(encodeParams({})).toEqual('')
  })

  test('escapes parameters', () => {
    expect(encodeParams({ '&?=': '&?=' })).toEqual('%26%3F%3D=%26%3F%3D')
  })

  test('orders parameters by name', () => {
    expect(encodeParams({ z: 'z', a: 'a' })).toEqual('a=a&z=z')
  })
})

describe('pluck', () => {
  test('basic example', () => {
    expect(pluck([{ a: 1, b: 2 }, { a: 4, b: 3 }], 'a')).toEqual([1, 4])
  })

  test('missing key', () => {
    expect(pluck([{ c: 1, b: 2 }, { a: 4, b: 3 }], 'a')).toEqual([undefined, 4])
  })

  test('empty array', () => {
    expect(pluck([], 'a')).toEqual([])
  })
})

describe('min', () => {
  test('with integers', () => {
    expect(min([10, 3, 100, -4])).toBe(-4)
  })

  test('with infinity', () => {
    expect(min([-Infinity, 0, Infinity])).toBe(-Infinity)
  })

  test('with strings', () => {
    expect(min(['bravo', 'alpha', 'charlie'])).toBe('alpha')
  })

  test('with mixed strings and numbers', () => {
    expect(min([99, '100'])).toBe(99)
    expect(min(['99', 100])).toBe('99')
  })
})

describe('max', () => {
  test('with integers', () => {
    expect(max([10, 3, 100, -4])).toBe(100)
  })

  test('with infinity', () => {
    expect(max([-Infinity, 0, Infinity])).toBe(Infinity)
  })

  test('with strings', () => {
    expect(max(['bravo', 'alpha', 'charlie'])).toBe('charlie')
  })

  test('with mixed strings and numbers', () => {
    expect(max([99, '100'])).toBe('100')
    expect(max(['99', 100])).toBe(100)
  })
})

describe('uniq', () => {
  test('basic example', () => {
    expect(uniq([1, 1, 2, 2, 2, 3, 3]).toSorted()).toEqual([1, 2, 3])
  })
})

describe('pick', () => {
  test('when all keys present', () => {
    expect(pick({ a: 1, b: 2, c: 3 }, ['a', 'b'])).toEqual({ a: 1, b: 2 })
  })

  test('when keys missing', () => {
    expect(pick({ a: 1, b: 2, c: 3 }, ['a', 'z'])).toEqual({ a: 1 })
  })
})

describe('debounce', () => {
  test('calls only once per debounce period', () => {
    let f = vi.fn()
    let debounced = debounce(f, 50)
    debounced('foo')
    debounced('bar')
    debounced('baz')
    expect(f).not.toHaveBeenCalled()
    vi.advanceTimersToNextTimer()
    expect(f).toHaveBeenCalledExactlyOnceWith('baz')
    vi.runAllTimers()
    expect(f).toHaveBeenCalledExactlyOnceWith('baz')
  })
})

describe('parseCSV', () => {
  test('unquoted values', () => {
    expect(parseCSV('a,b,c\n1,2,3\n')).toEqual([
      ['a', 'b', 'c'],
      ['1', '2', '3']
    ])
  })

  test('without trailing newline', () => {
    expect(parseCSV('a,b,c\n1,2,3')).toEqual([
      ['a', 'b', 'c'],
      ['1', '2', '3']
    ])
  })

  test('with quoted field', () => {
    expect(parseCSV('"a",b,c')).toEqual([['a', 'b', 'c']])
  })

  test('with escaped quote', () => {
    expect(parseCSV('"a""",b,c')).toEqual([['a"', 'b', 'c']])
  })

  test('with rogue quote', () => {
    expect(() => parseCSV('a",b,c')).toThrowError(/Unexpected double-quote/)
  })

  test('with CRLF', () => {
    expect(parseCSV('a,b,c\r\n1,2,3')).toEqual([
      ['a', 'b', 'c'],
      ['1', '2', '3']
    ])
  })

  test('with CR only', () => {
    expect(parseCSV('a,b,c\r1,2,3')).toEqual([
      ['a', 'b', 'c'],
      ['1', '2', '3']
    ])
  })

  test('empty input', () => {
    expect(parseCSV('')).toEqual([])
  })
})

// Source: https://stackoverflow.com/a/77278013/165783
const deepEqualsTestValues = [
  // primitives
  [null, null, true],
  [undefined, undefined, true],
  [null, undefined, false],
  [undefined, null, false],
  ['undefined', 'undefined', true],
  [1, 1, true],
  [1, 4, false],
  [3.123, 3.123, true],
  [3.1234567, 3.123, false],
  [false, false, true],
  [true, true, true],
  [true, false, false],
  [false, true, false],

  // objects
  [{}, {}, true],
  [{}, { test: 1 }, false],
  [{ test: 1 }, {}, false],
  [{ test: 1 }, { test: 1 }, true],
  [{ test: 1 }, { test: 2 }, false],
  [{ test: 1, deep: { test: 2 } }, { test: 1, deep: { test: 2 } }, true],
  [
    { test: 1, deep: { test: 'string' } },
    { test: 1, deep: { test: 2 } },
    false
  ],

  // arrays
  [[], [], true],
  [[], [1], false],
  [[1], [1], true],
  [[1, 2, 3], [1, 3, 'string'], false],
  [[1, 2, 'string'], [1, 3, 'string'], false],
  [[1, '2', null, { object: 1 }], [1, '2', null, { object: 1 }], true],
  [[1, 2, { object: 1 }], [1, 2, { object: 'string' }], false],
  [[[[]]], [[[]]], true],
  [[[[2]]], [[[2]]], true],
  [[[[2]]], [[[8]]], false],
  [[[], []], [[], []], true],
  [[[1, 2], [3]], [[1, 2], [3]], true],
  [[[1, 2], 3, [4]], [[1, 2], 3, [4]], true],
  [[[1, 2], 3, [{ object: 'deep' }]], [[1, 2], 3, [{ object: 'deep' }]], true],
  [[[1, 2], 'middle', [4]], [[1, 2], 3, ['end']], false],

  // mix (always false)
  ['', 0, false],
  ['0', 0, false],
  [undefined, 0, false],
  [null, 0, false],
  ['undefined', undefined, false],
  [NaN, 0, false],
  [{}, [], false],
  [{ 1: 'a' }, ['a'], false],
  [{ 1: 'a', 2: 'b' }, ['a', 'b'], false],
  [{ some: 'object' }, [{ some: 'object' }], false]
]
describe('deepEquals', () => {
  test.each(deepEqualsTestValues)(
    'should compare %s and %s (%s)',
    (a, b, expectedResult) => {
      expect(deepEquals(a, b)).toEqual(expectedResult)
    }
  )
})

describe('throttle', () => {
  test('responds to first call immediately, then once per period', () => {
    let f = vi.fn()
    let throttled = throttle(f, 50)
    throttled('foo')
    throttled('bar')
    throttled('baz')
    expect(f).toHaveBeenCalledExactlyOnceWith('foo')
    vi.advanceTimersToNextTimer()
    expect(f).toHaveBeenCalledTimes(2)
    expect(f).toHaveBeenLastCalledWith('baz')
    vi.runAllTimers()
    expect(f).toHaveBeenCalledTimes(2)
  })
})

describe('searchStringToRegex', () => {
  let testValues = [
    ['world', 'hello world', true],
    ['world', 'hello World', true],
    ['bye', 'hello World', false],
    ['/regex^{}[]!/', '/regex^{}[]!/', true],
    ['/regex^{}[]!/', '/regex^{}[]!', false]
  ]
  test.each(testValues)(
    'should search for \'%s\' in \'%s\' with result %s',
    (needle, haystack, expectedResult) => {
      expect(searchStringToRegex(needle).test(haystack)).toBe(expectedResult)
    }
  )
})

describe('matchParts', () => {
  let testValues = [
    ['Tomato Mate', /mat/gi, [['To', 'mat'], ['o ', 'Mat'], ['e', '']]],
    ['Tomato Mate', /foo/gi, [['Tomato Mate', '']]],
    ['Tomato Mate', /T/gi, [['', 'T'], ['oma', 't'], ['o Ma', 't'], ['e', '']]],
    ['Tomato Mate', /T/g, [['', 'T'], ['omato Mate', '']]]
  ]
  test.each(testValues)(
    'should search %s for %s',
    (haystack, regex, expectedResult) => {
      expect(matchParts(haystack, regex)).toEqual(expectedResult)
    }
  )

  test('fails with non-global regex', () => {
    expect(() => matchParts('foo', /foo/)).toThrowError()
  })
})

describe('capitalise', () => {
  let testValues = [
    ['', ''],
    ['a', 'A'],
    ['A', 'A'],
    ['cat', 'Cat'],
    [' cat', ' cat'],
    ['cat bird', 'Cat bird'],
    ['!cat', '!cat']
  ]
  test.each(testValues)(
    '\'%s\' => \'%s\'',
    (input, expectedResult) => {
      expect(capitalise(input)).toBe(expectedResult)
    })
})
