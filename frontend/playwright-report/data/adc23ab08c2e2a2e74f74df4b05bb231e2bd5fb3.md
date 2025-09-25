# Page snapshot

```yaml
- generic [ref=e4]:
  - img [ref=e6]
  - heading "Что-то пошло не так" [level=1] [ref=e8]
  - paragraph [ref=e9]: Произошла неожиданная ошибка. Попробуйте обновить страницу или вернуться на главную.
  - generic [ref=e10]:
    - heading "Детали ошибки:" [level=3] [ref=e11]
    - generic [ref=e12]: "ReferenceError: SortableTableHeader is not defined at SamplesPage (http://localhost:3001/src/features/samples/pages/SamplesPage.tsx?t=1758776208062:26:33) at RenderedRoute (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:4088:5) at Outlet (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:4494:26) at main (<anonymous>) at div (<anonymous>) at div (<anonymous>) at Layout (<anonymous>) at RenderedRoute (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:4088:5) at Routes (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:4558:5) at Router (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:4501:15) at BrowserRouter (http://localhost:3001/node_modules/.vite/deps/react-router-dom.js?v=ac522a00:5247:5) at ErrorBoundary (http://localhost:3001/src/shared/components/ErrorBoundary/ErrorBoundary.tsx:8:5) at App (<anonymous>)"
  - generic [ref=e13]:
    - button "Попробовать снова" [ref=e14] [cursor=pointer]:
      - img [ref=e15] [cursor=pointer]
      - text: Попробовать снова
    - button "На главную" [ref=e20] [cursor=pointer]:
      - img [ref=e21] [cursor=pointer]
      - text: На главную
```