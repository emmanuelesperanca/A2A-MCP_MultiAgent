# 🧪 Exemplo de Resposta com Markdown - Teste

## Como Testar o Suporte a Markdown

### 1. Perguntar ao Agente de Desenvolvimento

**Pergunta de exemplo:**
```
"Me mostre como criar uma função Python que calcula fatorial"
```

**Resposta esperada do agente Carlos:**

---

## Como Calcular Fatorial em Python

Olá! Vou te mostrar como criar uma função para calcular o **fatorial** de um número em Python.

### Método 1: Recursivo

```python
def fatorial_recursivo(n):
    """
    Calcula o fatorial de n usando recursão
    
    Args:
        n (int): Número inteiro positivo
        
    Returns:
        int: Fatorial de n
    """
    if n == 0 or n == 1:
        return 1
    return n * fatorial_recursivo(n - 1)

# Exemplo de uso
resultado = fatorial_recursivo(5)
print(f"5! = {resultado}")  # Output: 5! = 120
```

### Método 2: Iterativo

```python
def fatorial_iterativo(n):
    """
    Calcula o fatorial de n usando iteração
    
    Args:
        n (int): Número inteiro positivo
        
    Returns:
        int: Fatorial de n
    """
    resultado = 1
    for i in range(1, n + 1):
        resultado *= i
    return resultado

# Exemplo de uso
resultado = fatorial_iterativo(5)
print(f"5! = {resultado}")  # Output: 5! = 120
```

### Método 3: Usando biblioteca (mais eficiente)

```python
import math

# Forma mais simples e eficiente
resultado = math.factorial(5)
print(f"5! = {resultado}")  # Output: 5! = 120
```

### Comparação de Performance

| Método      | Complexidade | Vantagem                    | Desvantagem            |
|-------------|--------------|-----------------------------|-----------------------|
| Recursivo   | O(n)         | Código elegante             | Stack overflow em n grande |
| Iterativo   | O(n)         | Sem limite de recursão      | Código menos elegante |
| math.factorial | O(n)      | **Mais rápido e confiável** | Requer biblioteca     |

> **Recomendação**: Para uso em produção, prefira `math.factorial()` por ser otimizado e testado.

### Validação de Entrada

Para tornar suas funções mais robustas, adicione validação:

```python
def fatorial_seguro(n):
    """Versão com validação de entrada"""
    if not isinstance(n, int):
        raise TypeError("n deve ser um número inteiro")
    if n < 0:
        raise ValueError("n deve ser não-negativo")
    
    resultado = 1
    for i in range(1, n + 1):
        resultado *= i
    return resultado

# Testando
try:
    print(fatorial_seguro(5))   # ✅ 120
    print(fatorial_seguro(-1))  # ❌ ValueError
except ValueError as e:
    print(f"Erro: {e}")
```

### Próximos Passos

1. Teste os três métodos e compare a performance
2. Implemente testes unitários com `pytest`
3. Considere usar `@lru_cache` para otimizar recursão

---

Espero ter ajudado! Se tiver mais dúvidas sobre desenvolvimento em Python, estou à disposição. 😊

---

## 2. Resultado Visual Esperado

Ao fazer essa pergunta no chat, você verá:

✅ **Títulos** formatados com bordas inferiores  
✅ **Código Python** com syntax highlighting colorido  
✅ **Botão "Copiar"** em cada bloco de código  
✅ **Tabela** com hover effects em linhas  
✅ **Blockquote** com fundo roxo claro e borda roxa  
✅ **Listas** numeradas e com bullet points  
✅ **Negrito** e `código inline` destacados  

## 3. Outras Perguntas de Teste

### Teste com Lista Simples
```
"Quais são as melhores práticas de desenvolvimento Python?"
```

### Teste com Tabela
```
"Compare Python, JavaScript e TypeScript"
```

### Teste com Blockquote
```
"Me dê uma citação inspiradora sobre programação"
```

### Teste com Imagens (se aplicável)
```
"Me mostre um diagrama de arquitetura"
```

## 4. Verificação Técnica

### No Console do Navegador (F12):

```javascript
// Verificar se bibliotecas foram carregadas
console.log(typeof marked);     // Deve retornar "object"
console.log(typeof hljs);       // Deve retornar "object"

// Testar renderização manual
const html = marked.parse('# Teste\n- Item 1\n- Item 2');
console.log(html);
```

### Verificar CSS:

```javascript
// Verificar se estilos de Markdown estão aplicados
const styles = getComputedStyle(document.querySelector('.message-text'));
console.log(styles.lineHeight);  // Deve ser "1.6"
```

## 5. Troubleshooting Durante Teste

### Markdown não renderiza:
- ❌ Verificar console para erros de carregamento de CDN
- ✅ Recarregar página com Ctrl+F5
- ✅ Verificar se `marked.js` foi carregado na aba Network

### Código sem cores:
- ❌ Linguagem não especificada no bloco
- ✅ Usar \`\`\`python em vez de apenas \`\`\`
- ✅ Verificar se `highlight.js` foi carregado

### Botão copiar não aparece:
- ❌ CSS não carregado
- ✅ Passar mouse sobre o código (botão tem opacity: 0)
- ✅ Verificar DevTools por erros JavaScript

---

**Versão:** 1.0  
**Data:** 22 de Outubro de 2025
