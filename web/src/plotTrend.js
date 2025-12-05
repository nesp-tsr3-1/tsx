import {
  Chart,
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
} from 'chart.js'

Chart.register(
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
)

let solidFill = 'rgba(230,230,230,0.5)'
let stripeFill = createDiagonalPattern('grey', 1, 4)

// see: https://www.chartjs.org/docs/latest/configuration/canvas-background.html#color
const backgroundColorPlugin = {
  id: 'canvasBackgroundColor',
  beforeDraw: (chart, args, options) => {
    const { ctx } = chart
    ctx.save()
    ctx.globalCompositeOperation = 'destination-over'
    ctx.fillStyle = options.color || '#ffffff'
    ctx.fillRect(0, 0, chart.width, chart.height)
    ctx.restore()
  }
}

export function plotTrend(data, dom, options) {
  let plotData = generateTrendPlotData(data, options)

  let minYear = plotData.labels[0]

  let plot = new Chart(dom.getContext('2d'), {
    type: 'line',
    data: plotData,
    plugins: [backgroundColorPlugin],
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        },
        canvasBackgroundColor: {
          color: 'white'
        }
      },
      maintainAspectRatio: true,
      scales: {
        yAxis: {
          display: true,
          position: 'left',
          grid: {
            display: true
          },
          ticks: {
            callback: function(label, index, labels) {
              // Show appropriate number of decimal places
              let delta = (labels.length > 1) ? Math.abs(labels[1].value - labels[0].value) : 0
              let decimalPlaces = (delta > 0) ? Math.min(5, Math.max(1, -Math.floor(Math.log10(delta)))) : 1
              return (+label).toFixed(decimalPlaces)
            }
          },
          title: {
            display: true,
            text: minYear ? 'Index (' + minYear + ' = 1)' : ''
          },
          suggestedMax: 1.4,
          suggestedMin: 0
        },
        xAxis: {
          title: {
            display: true,
            text: 'Year'
          }
        }
      }
    }
  })

  return plot
}

function createDiagonalPattern(color = 'black', width = 2, gap = 8) {
  let size = width + gap

  let shape = document.createElement('canvas')
  shape.width = size
  shape.height = size
  let c = shape.getContext('2d')

  c.strokeWidth = width
  c.strokeStyle = color
  for(let x = 0; x < 3; x++) {
    let x0 = (x - 1) * size
    c.beginPath()
    c.moveTo(x0, 0)
    c.lineTo(x0 + size, size)
    c.stroke()
  }
  // create the pattern from the shape
  return c.createPattern(shape, 'repeat')
}

export function generateTrendPlotData(data, options) {
  options = {
    ignoreNumSpecies: false,
    ...options
  }

  let series = data.split('\n')
    .slice(1) // Ignore first line
    .filter(line => line.trim().length > 0 && !/NA/.test(line)) // Ignore empty or NA lines
    .map(line => line.split(' '))

  let labels = series.map(x => parseInt(x[0].replace(/"/g, '')))
  let index = series.map(x => parseFloat(x[1]))
  let lowerCI = series.map(x => parseFloat(x[2]))
  let upperCI = series.map(x => parseFloat(x[3]))
  let numSpecies
  if(options.ignoreNumSpecies) {
    numSpecies = series.map(x => -1)
  } else {
    numSpecies = series.map(x => parseInt(x[4] ?? -1))
  }

  let isSingleSpecies = index.map((x, i) => (lowerCI[i] === upperCI[i]) || (numSpecies[i] === 1))
  let solidIndex = index.map((x, i) => !isSingleSpecies[i] || (i > 0 && !isSingleSpecies[i - 1]) || (i < index.length - 1 && !isSingleSpecies[i + 1]) ? x : undefined)
  let dashedIndex = index.map((x, i) => isSingleSpecies[i] ? x : undefined)

  let allSingleSpecies = isSingleSpecies.every(x => x)

  let plotData = {
    labels: labels,
    datasets: [{
      label: 'TSX',
      borderColor: '#36699e',
      backgroundColor: 'black',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      data: solidIndex
    }, {
      label: 'TSX',
      display: false,
      borderColor: '#36699e',
      backgroundColor: 'black',
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      borderDash: [5, 5],
      data: dashedIndex
    }, {
      label: 'Confidence Interval (low)',
      backgroundColor: allSingleSpecies ? stripeFill : solidFill,
      fill: false,
      pointRadius: 0,
      lineTension: 0,
      borderColor: '#0000',
      borderWidth: 1,
      data: lowerCI
    }, {
      label: 'Confidence Interval (high)',
      borderColor: solidFill,
      backgroundColor: allSingleSpecies ? stripeFill : solidFill,
      fill: 2, // Fill between this dataset and dataset[1], i.e. between low & hi CI
      pointRadius: 0,
      lineTension: 0,
      borderWidth: 1,
      data: upperCI
    }]
  }

  return plotData
}

export function trendDiagnosticsText(diagnosticsData) {
  let parts = []
  let gamCount = diagnosticsData.model_counts.gam
  let chainCount = diagnosticsData.model_counts.chain
  let totalCount = gamCount + chainCount

  if(gamCount > 0) {
    parts.push(`general additive model (${Math.round(gamCount * 100 / totalCount)}%)`)
  }

  if(chainCount > 0) {
    parts.push(`log-linear interpolation (${Math.round(chainCount * 100 / totalCount)}%)`)
  }

  if(gamCount == 0 && chainCount == 0) {
    parts.push('none')
  }

  return 'Models used: ' + parts.join(', ')
}
