<script setup>
// Client-only CKEditor 5 wrapper. Requires the `ckeditor5` npm package
// (`npm install ckeditor5`). If it isn't installed or fails to load, this
// gracefully falls back to a plain textarea so tickets always work.
const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "Write your message…" },
});
const emit = defineEmits(["update:modelValue"]);

const holder = ref(null);
const editor = ref(null);
const failed = ref(false);
let applyingRemote = false;

function base64UploadAdapter(loader) {
  return {
    upload: () =>
      loader.file.then(
        (file) =>
          new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve({ default: reader.result });
            reader.onerror = reject;
            reader.readAsDataURL(file);
          })
      ),
    abort() {},
  };
}

onMounted(async () => {
  try {
    await import("ckeditor5/ckeditor5.css");
    const {
      ClassicEditor, Essentials, Paragraph, Heading, Bold, Italic, Underline,
      Strikethrough, Code, Link, List, BlockQuote, CodeBlock, Image, ImageToolbar,
      ImageCaption, ImageStyle, ImageUpload, ImageResize, Table, TableToolbar,
      Autoformat, PasteFromOffice,
    } = await import("ckeditor5");

    const instance = await ClassicEditor.create(holder.value, {
      licenseKey: "GPL",
      plugins: [
        Essentials, Paragraph, Heading, Bold, Italic, Underline, Strikethrough,
        Code, Link, List, BlockQuote, CodeBlock, Image, ImageToolbar, ImageCaption,
        ImageStyle, ImageUpload, ImageResize, Table, TableToolbar, Autoformat, PasteFromOffice,
      ],
      toolbar: [
        "heading", "|", "bold", "italic", "underline", "code", "link", "|",
        "bulletedList", "numberedList", "blockQuote", "codeBlock", "|",
        "uploadImage", "insertTable", "|", "undo", "redo",
      ],
      placeholder: props.placeholder,
      image: {
        toolbar: ["imageTextAlternative", "imageStyle:inline", "imageStyle:block", "imageStyle:side"],
      },
      table: { contentToolbar: ["tableColumn", "tableRow", "mergeTableCells"] },
    });

    // Wire the v-model binding first. This is the only thing that actually
    // matters for a reply to be captured — do it before any non-critical
    // setup so a failure below can never leave the editor visible-but-mute.
    instance.setData(props.modelValue || "");
    instance.model.document.on("change:data", () => {
      applyingRemote = true;
      emit("update:modelValue", instance.getData());
      applyingRemote = false;
    });
    editor.value = instance;

    // Best-effort image upload support — not required for text replies, so
    // it must never be able to knock the editor into the "failed" fallback.
    try {
      instance.plugins.get("FileRepository").createUploadAdapter = base64UploadAdapter;
    } catch (e) {
      // Image uploads just won't work; typing/sending a reply still does.
    }
  } catch (e) {
    // Real init failure (e.g. the ckeditor5 package isn't installed). Tear
    // down any partially-created instance so it can't linger on screen
    // alongside the fallback textarea.
    try { editor.value?.destroy?.(); } catch (_) { /* noop */ }
    editor.value = null;
    failed.value = true;
  }
});

watch(
  () => props.modelValue,
  (v) => {
    if (editor.value && !applyingRemote && v !== editor.value.getData()) {
      editor.value.setData(v || "");
    }
  }
);

onBeforeUnmount(() => {
  try { editor.value?.destroy?.(); } catch (e) { /* noop */ }
});

function onTextarea(e) {
  emit("update:modelValue", e.target.value);
}
</script>

<template>
  <ClientOnly>
    <div class="bk-rich-wrap">
      <div v-if="!failed" ref="holder"></div>
      <textarea
        v-else
        :value="modelValue"
        :placeholder="placeholder"
        rows="6"
        class="w-full bg-[#1a1a1a] border border-white/[0.12] rounded-xl p-3 text-[#f0f0f0] placeholder-[#666] focus:outline-none focus:border-[#c9ff47]"
        @input="onTextarea"
      />
    </div>
    <template #fallback>
      <div class="rounded-xl border border-white/[0.12] bg-[#1a1a1a] h-32 grid place-items-center text-[#666] text-sm">
        Loading editor…
      </div>
    </template>
  </ClientOnly>
</template>
