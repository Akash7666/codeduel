// Uses the locally-bundled CodeMirror exposed on window.CodeDuelCM (from cm-bundle.js)
const { EditorView, EditorState, basicSetup, Compartment, python } = window.CodeDuelCM;

const readOnlyCompartment = new Compartment();
let view = null;

function mountEditor(targetEl, initialContent = "") {
  const state = EditorState.create({
    doc: initialContent,
    extensions: [
      basicSetup,
      python(),
      readOnlyCompartment.of(EditorState.readOnly.of(true)),
    ],
  });
  view = new EditorView({ state, parent: targetEl });
  return view;
}

function setEditorContent(content) {
  if (!view) return;
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: content },
  });
}

function setEditorReadOnly(readOnly) {
  if (!view) return;
  view.dispatch({
    effects: readOnlyCompartment.reconfigure(EditorState.readOnly.of(readOnly)),
  });
}

function getEditorContent() {
  if (!view) return "";
  return view.state.doc.toString();
}