import BpmnModeler from 'bpmn-js/lib/Modeler';

import {
  debounce
} from 'min-dash';

import diagramXML from '../resources/diagram.bpmn';

const container = document.getElementById('container');

const bpmnModeler = new BpmnModeler({
  container,
  keyboard: {
    bindTo: document
  }
});

const downloadLink = document.getElementById('download-diagram');
const downloadSvgLink = document.getElementById('download-svg');

const url = new URL(window.location.href);

const persistentURL = url.searchParams.get('url');

const initialDiagram = (() => {
  try {
    return persistentURL || diagramXML;
  } catch (err) {
    return diagramXML;
  }
})();


function openDiagram(diagram) {

  bpmnModeler.importXML(diagram)
    .then(({ warnings }) => {
      if (warnings.length) {
        console.warn(warnings);
      }

      const canvas = bpmnModeler.get('canvas');

      canvas.zoom('fit-viewport');

      document.body.classList.remove('with-error');
      document.body.classList.add('with-diagram');
    })
    .catch(err => {
      document.body.classList.add('with-error');
      document.body.classList.remove('with-diagram');

      console.error(err);
    });
}


function fetchDiagram(url) {

  fetch(url)
    .then(response => response.text())
    .then(openDiagram)
    .catch(console.error);
}


const debouncedFetchDiagram = debounce(fetchDiagram, 500);

debouncedFetchDiagram(initialDiagram);

const editor = document.querySelector('#editor');

editor.addEventListener('input', () => {
  const url = editor.value;

  if (url) {
    url.searchParams.set('url', url);
  } else {
    url.searchParams.delete('url');
  }

  window.history.replaceState({}, '', url);

  debouncedFetchDiagram(url);
});

editor.value = persistentURL || '';

// --

async function exportArtifacts() {

  try {

    const { svg } = await bpmnModeler.saveSVG();

    setEncoded(downloadSvgLink, 'diagram.svg', svg);
  } catch (err) {

    console.error('could not save BPMN 2.0 diagram', err);
  }

  try {

    const { xml } = await bpmnModeler.saveXML({ format: true });

    setEncoded(downloadLink, 'diagram.bpmn', xml);
  } catch (err) {

    console.error('could not save BPMN 2.0 diagram', err);
  }
}

function setEncoded(link, name, data) {
  const encodedData = encodeURIComponent(data);

  if (data) {
    link.classList.add('active');
    link.href = 'data:application/bpmn20-xml;charset=UTF-8,' + encodedData;
    link.download = name;
  } else {
    link.classList.remove('active');
  }
}

bpmnModeler.on('commandStack.changed', exportArtifacts);
