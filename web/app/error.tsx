"use client";

export default function CatalogError() {
  return (
    <main>
      <h1>Каталог</h1>
      <p>Не удалось загрузить каталог.</p>
      <button type="button" onClick={() => window.location.reload()}>
        Повторить
      </button>
    </main>
  );
}
