export type Product = {
  id: string;
  title: string;
  image_url: string;
  created_at: string;
};

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8080";

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_URL}/api/products`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ответил ${response.status}`);
  }
  return response.json();
}
