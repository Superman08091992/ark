<script>
  let count = 0;
  function increment() {
    count += 1;
  }
</script>

<main>
  <h1>Vite 7 + Svelte 5 Test</h1>
  <button on:click={increment}>
    Count: {count}
  </button>
  <p>Testing Vite 7 compatibility</p>
</main>

<style>
  main {
    text-align: center;
    padding: 2rem;
  }
  button {
    font-size: 1.2rem;
    padding: 0.5rem 1rem;
  }
</style>
