import { getProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CatalogPage() {
  const products = await getProducts();

  return (
    <main>
      <h1>Каталог</h1>
      {products.length === 0 ? (
        <p>Товаров пока нет</p>
      ) : (
        <ul>
          {products.map((product) => (
            <li key={product.id}>
              <img src={product.image_url} alt={product.title} width={160} loading="lazy" />
              <div>{product.title}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
