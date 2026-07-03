// Venues the current user owns or manages (my_role != null). Client-side.
export const useMyVenues = () => {
  const api = useApi();
  return useAsyncData(
    "my-venues",
    async () => {
      const res = await api("/api/futsals/", { query: { page_size: 100 } });
      return res.results.filter((v) => v.my_role);
    },
    { server: false }
  );
};
