export function useLocationTheme(slug: Ref<string | null | undefined> | string | null | undefined) {
  const slugRef = isRef(slug) ? slug : ref(slug ?? null)

  useHead(() => ({
    bodyAttrs: {
      'data-location': slugRef.value ?? undefined,
    },
  }))
}
