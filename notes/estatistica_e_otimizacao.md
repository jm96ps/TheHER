# Conceitos Estatísticos e Métodos de Otimização — Referência do Autor

> **Uso interno.** Notas para o autor do modelo `hydrogen.py`. Não revisado para publicação.

---

## Sumário

1. [Fundamentos de Fitting](#1-fundamentos-de-fitting)
2. [Mínimos Quadrados e Variantes](#2-mínimos-quadrados-e-variantes)
3. [Fitting em Log-espaço](#3-fitting-em-log-espaço)
4. [Pesos e Incertezas nos Dados](#4-pesos-e-incertezas-nos-dados)
5. [Perda Robusta (Robust Loss)](#5-perda-robusta-robust-loss)
6. [Busca Global — Evolução Diferencial](#6-busca-global--evolução-diferencial)
7. [Busca Local — Levenberg-Marquardt e least_squares](#7-busca-local--levenberg-marquardt-e-least_squares)
8. [Multi-start](#8-multi-start)
9. [Critérios de Seleção de Modelo](#9-critérios-de-seleção-de-modelo)
10. [Incerteza dos Parâmetros](#10-incerteza-dos-parâmetros)
11. [Análise de Tafel com Janela Deslizante](#11-análise-de-tafel-com-janela-deslizante)
12. [Cobertura Superficial θ e Steady-state](#12-cobertura-superficial-θ-e-steady-state)
13. [Referências](#13-referências)

---

## 1. Fundamentos de Fitting

### O que é fitting?

Fitting (ou ajuste) é o processo de encontrar os parâmetros **p** de um modelo **f(x; p)** que minimizam a discrepância entre a predição e os dados observados `(xi, yi)`:

```
min_p  Sum_i  [yi - f(xi; p)]^2
```

No contexto eletroquímico deste projeto, `x` é o potencial aplicado (V) e `y` é a densidade de corrente (A), e `f` é a expressão cinética do HER (Volmer-Heyrovsky ou Volmer-Heyrovsky-Tafel).

### Resíduo

O resíduo de um ponto `i` é:

```
ri = yi - f(xi; p)
```

O objetivo é tornar todos os resíduos pequenos simultaneamente.

---

## 2. Mínimos Quadrados e Variantes

### Mínimos Quadrados Ordinários (OLS)

```
chi2 = Sum_i ri^2
```

Minimizar `chi2` é equivalente à máxima verossimilhança gaussiana com variância constante.

### Mínimos Quadrados Ponderados (WLS)

Quando cada ponto tem uma incerteza diferente `sigma_i`, os resíduos são ponderados:

```
chi2 = Sum_i (ri / sigma_i)^2  =  Sum_i wi * ri^2,    onde wi = 1/sigma_i
```

**No código (`_fit_weights`):**
```python
sigma = max(relative_error * |I|,  current_noise)
weight = 1.0 / sigma
```
- `relative_error` (padrão 3%): captura ruído proporcional à magnitude da corrente.
- `current_noise`: piso absoluto para evitar peso infinito em `I ≈ 0`.

> **Por que ponderar?** Correntes de alta magnitude têm mais variação absoluta; sem pesos, o fitting seria dominado pelos pontos mais extremos e negligenciaria a região cinética de interesse.

### Chi-quadrado Reduzido

```
chi2_red = chi2 / nu,     nu = N - p
```

Onde `N` = número de pontos e `p` = número de parâmetros livres (`nfree`).

- `chi2_red ≈ 1`: o modelo descreve os dados dentro da incerteza esperada.
- `chi2_red >> 1`: underfitting — o modelo é inadequado.
- `chi2_red << 1`: overfitting ou incertezas superestimadas.

### R² (Coeficiente de Determinação)

```
R² = 1 - SS_res / SS_tot

SS_res = Sum (yi - y_hat_i)^2
SS_tot = Sum (yi - y_mean)^2
```

- `R² = 1`: ajuste perfeito.
- `R² < 0`: o modelo é pior que a média dos dados.

> **Cuidado:** R² não é um bom critério para comparar modelos com diferente número de parâmetros. Prefira AIC/BIC (ver §9).

---

## 3. Fitting em Log-espaço

### Por que usar log-espaço para constantes de velocidade?

As constantes cinéticas (`k1`, `k1r`, `k2`, etc.) variam em muitas ordens de grandeza (ex.: `1e-20` a `1e-2`). Otimizar diretamente em escala linear:
- Cria superfícies de custo assimétricas e mal-condicionadas.
- Não garante positividade dos parâmetros.

A solução é parametrizar em log-espaço:

```
log_k = ln(k)   -->   k = exp(log_k)
```

**No código (`_add_log_rate`):**
```python
params.add(f"log_{name}", value=np.log(k0), min=ln(k_min), max=ln(k_max))
params.add(name, expr=f"exp(log_{name})")   # parâmetro derivado, não livre
```

O otimizador trabalha em `log_k` (domínio real, bem condicionado). O parâmetro `k` é calculado automaticamente via expressão.

### Benefícios

| Direto (linear)              | Log-espaço                     |
|------------------------------|--------------------------------|
| k > 0 não garantido          | k > 0 por construção           |
| Gradiente ~0 para k pequeno  | Gradiente uniforme em log      |
| Hessiana ill-conditioned     | Hessiana mais bem condicionada |
| Difícil para multi-escala    | Escala uniforme                |

---

## 4. Pesos e Incertezas nos Dados

### Modelo de Ruído Assumido

```
sigma_i = max(epsilon_rel * |Ii|,  sigma_min)
```

- `epsilon_rel`: erro relativo (3% por padrão) — captura ruído multiplicativo.
- `sigma_min = 1e-6 × max(|I|)`: piso absoluto para evitar divisão por zero em correntes próximas de zero.

### Implicação Estatística

Esse modelo de ruído assume que:
- A incerteza é aproximadamente proporcional ao sinal (ruído multiplicativo / heteroscedástico).
- Há um ruído de fundo independente do sinal.

Isso é razoável para medições de corrente eletroquímica com potenciostatos modernos.

---

## 5. Perda Robusta (Robust Loss)

### Motivação

O fitting padrão com `chi2 = Sum ri^2` é muito sensível a **outliers** — um único ponto com ruído grande pode distorcer todo o ajuste. Funções de perda robustas atenuam outliers.

### Funções de Perda Disponíveis (`scipy.optimize.least_squares`)

Seja `z = ri^2` o quadrado do resíduo escalado. A perda robusta `rho(z)` substitui `z`:

| Nome       | `rho(z)`                              | Comportamento                     |
|------------|---------------------------------------|-----------------------------------|
| `linear`   | `z`                                   | OLS puro, sensível a outliers     |
| `soft_l1`  | `2*(sqrt(1+z) - 1)`                   | Transição suave L2 → L1           |
| `huber`    | `z` se `z<=1`, `2*sqrt(z)-1` se `z>1`| L2 perto de zero, L1 para outlier |
| `cauchy`   | `ln(1 + z)`                           | Muito robusto, pode ser instável  |
| `arctan`   | `arctan(z)`                           | Ainda mais robusto                |

**No código:**
```python
fit_kws = {
    "loss": robust_loss,        # padrão: "soft_l1"
    "f_scale": robust_f_scale,  # limiar de inlier (padrão: 1.0)
    "x_scale": "jac",           # escalamento automático via Jacobiano
}
```

### Parâmetro `f_scale`

Define o limiar (em unidades de resíduo normalizado) abaixo do qual um ponto é considerado "inlier":
- Resíduos `< f_scale`: tratados com perda quadrática (L2).
- Resíduos `> f_scale`: tratados com perda robusta (L1-like).

### `x_scale = "jac"`

O otimizador calcula automaticamente a escala de cada parâmetro usando o Jacobiano, equilibrando parâmetros com magnitudes muito diferentes. Equivalente a um pré-condicionamento da matriz Hessiana.

---

## 6. Busca Global — Evolução Diferencial

### Problema

A superfície de custo do HER tem múltiplos mínimos locais porque os parâmetros cinéticos estão acoplados não-linearmente. Um otimizador local pode convergir para uma solução subótima dependendo do ponto inicial.

### Evolução Diferencial (DE)

Algoritmo estocástico evolutivo global. Mantém uma **população** de candidatos e gera novos candidatos por mutação e recombinação:

```
v = xa + F * (xb - xc)                       # mutação
candidato[i][j] = v[j] se rand<CR, senão xi[j]  # recombinação (crossover)
```

- `F` (fator de escala) e `CR` (taxa de cruzamento) são hiperparâmetros.
- Não requer gradiente — funciona em espaços descontínuos ou não-diferenciáveis.
- Convergência garantida em distribuição para o mínimo global (mas lenta).

**No código:**
```python
global_result = her_model.fit(
    y_data, initial_params, x=x_data,
    method="differential_evolution",
    max_nfev=30000,
)
```

> A DE aqui é usada apenas para **localizar a bacia de atração** do mínimo global. O refinamento preciso é feito pelo otimizador local (`least_squares`).

### Custo Computacional

DE com `max_nfev=30000` avalia o modelo ~30 mil vezes. Para modelos baratos (< 1 ms por avaliação), isso leva segundos. Para modelos caros, use `n_starts` com multi-start local e `use_global_search=False`.

---

## 7. Busca Local — Levenberg-Marquardt e `least_squares`

### Levenberg-Marquardt (LM)

Algoritmo híbrido entre Gauss-Newton e gradiente descendente:

```
(J^T J + lambda * I) * delta_p = J^T * r
```

- `J` = Jacobiano (dr_i/dp_j)
- `lambda = 0`: puro Gauss-Newton (rápido perto da solução)
- `lambda >> 0`: gradiente descendente (estável longe da solução)
- `lambda` é ajustado adaptativamente a cada iteração.

LM é o método padrão do `lmfit` e funciona bem para problemas de mínimos quadrados não-lineares com parâmetros sem restrições de caixa.

### `scipy.optimize.least_squares` — Trust-Region Reflective (TRF)

Método padrão quando há **bounds** (limites) nos parâmetros:

```
min_p  Sum_i rho(ri^2 / f_scale^2)
sujeito a:  lb <= p <= ub
```

- Respeita os limites de `log_k` definidos pelos bounds físicos de cada constante.
- Com `loss = "soft_l1"`, minimiza uma versão robustificada.
- TRF resolve subproblemas de confiança localmente — mais estável que LM com bounds.

---

## 8. Multi-start

### Por que usar?

Mesmo com busca global, pode ser vantajoso repetir o fitting com vários pontos iniciais aleatórios para:
- Confirmar convergência para o mesmo mínimo (indicador de robustez).
- Encontrar mínimos alternativos com chi2 similar (degenerescência paramétrica).
- Amostrar a distribuição de soluções quando a superfície tem platôs amplos.

**No código:**
```python
for _ in range(n_starts):
    initial_params = self._make_log_params(model_type)  # aleatorio em log-espaco
    ...
    candidates.append(local_result)

self.result_model = min(candidates, key=lambda r: r.chisqr)
```

A inicialização aleatória usa `rnd()` — amostragem uniforme em log10-espaço para cobertura uniforme de muitas ordens de grandeza.

---

## 9. Critérios de Seleção de Modelo

Quando dois modelos têm chi2 similares mas diferente número de parâmetros, usa-se critérios penalizados.

### AIC — Akaike Information Criterion

```
AIC = chi2 + 2p
```

Onde `p` = número de parâmetros livres. Penaliza modelos mais complexos. Baseado na teoria da informação (distância Kullback-Leibler).

### BIC — Bayesian Information Criterion

```
BIC = chi2 + p * ln(N)
```

Penaliza mais fortemente que o AIC quando `N > 7`. Derivado de argumento bayesiano (probabilidade a posteriori do modelo).

### Regra de Uso

- Prefira o modelo com **menor AIC ou BIC**.
- Delta_AIC > 10 entre dois modelos: forte evidência contra o modelo mais alto.
- Delta_AIC < 2: modelos essencialmente equivalentes; prefira o mais simples.

| Critério | Penalidade     | Quando usar                              |
|----------|----------------|------------------------------------------|
| AIC      | `2p`           | Predição, datasets grandes               |
| BIC      | `p * ln(N)`    | Seleção de modelo verdadeiro, parsimônia |

> No código (`get_stats`), ambos são reportados pelo `lmfit` diretamente.

---

## 10. Incerteza dos Parâmetros

### Matriz de Covariância

Após convergência, a incerteza dos parâmetros é estimada pela inversa da matriz Hessiana (aproximada via Jacobiano):

```
Cov(p) ≈ sigma^2 * (J^T J)^{-1}
```

A incerteza padrão de cada parâmetro é:

```
delta_pi = sqrt(Cov(p)_ii)
```

O `lmfit` reporta isso no `fit_report()` como `stderr`.

### Cuidados

- As incertezas são válidas na **aproximação linear** (elipse gaussiana em torno do mínimo).
- Para parâmetros muito acoplados ou superfícies não-parabólicas, use **profile likelihood** ou **MCMC** (não implementado aqui).
- A incerteza em `log_k` se propaga para `k`:

```
delta_k = k * delta(log_k)
```

### Correlações entre Parâmetros

Parâmetros com correlação alta (|rho| > 0.9) indicam degenerescência: o modelo pode ser ajustado igualmente bem com combinações diferentes desses parâmetros → o modelo pode estar sobreparametrizado.

---

## 11. Análise de Tafel com Janela Deslizante

### Inclinação de Tafel

A relação de Tafel descreve a variação do potencial com o logaritmo da corrente na região de transferência de carga:

```
E = a + b * log|I|
```

A inclinação de Tafel `b` (em mV/dec) é diretamente relacionada ao mecanismo de reação:

| Inclinação (mV/dec) | Etapa limitante             |
|---------------------|-----------------------------|
| ~120                | Volmer (adsorção de H)      |
| ~40                 | Heyrovsky (desorção eletroquímica) |
| ~30                 | Tafel (recombinação homolítica) |

### Janela Deslizante (Rolling Window)

Em vez de um único ajuste linear em toda a curva (que mistura regiões com mecanismos diferentes), faz-se regressão linear em janelas locais:

```python
for i in range(n - window_size + 1):
    E_window = E[i : i + window_size]
    logI_window = log10(|I|[i : i + window_size])
    slope, intercept, ... = linregress(logI_window, E_window)
    b_local = abs(slope) * 1000   # mV/dec
```

O resultado é `b(E)` — a inclinação de Tafel **como função do potencial**, revelando transições mecânicas ao longo da varredura.

### Método por Gradiente Numérico

O código também oferece:
```python
slope = dE / d(log|I|) = gradient(E) / gradient(log|I|)
```
Mais ruidoso (sensível a oscilações pontuais), mas não requer escolha de tamanho de janela. Útil como verificação rápida.

---

## 12. Cobertura Superficial θ e Steady-state

### Definição de θ

θ = fração de sítios ativos do eletrodo ocupados por H adsorvido (H*).
`1 - θ` = fração de sítios vazios.
**Limites físicos:** `0 ≤ θ ≤ 1`.

### Condição de Steady-state

Em estado estacionário, `dθ/dt = 0`. Para o modelo simplificado (Volmer-Heyrovsky):

```
r_Volmer = r_Heyrovsky

k1*(1-θ)*exp(-βv*F*E/RT) - k1r*θ*exp((1-βv)*F*E/RT)
 = k2*θ*exp(-βh*F*E/RT) - k2r*(1-θ)*exp((1-βh)*F*E/RT)
```

Resolvendo analiticamente para θ:

```
θ = [k1*exp(-βv*u) + k2r*exp((1-βh)*u)] /
    [k1*exp(-βv*u) + k1r*exp((1-βv)*u) + k2*exp(-βh*u) + k2r*exp((1-βh)*u)]
```

Onde `u = F*E / (R*T)` é o potencial adimensional.

### Modelo Completo (VHT — com etapa de Tafel)

A equação de steady-state para o mecanismo Volmer-Heyrovsky-Tafel resulta em uma **equação quadrática** em θ:

```
a*θ² + b*θ + c = 0

a = -2*k3 + 2*k3r
b = -k1*exp(-βv*u) - k1r*exp((1-βv)*u) - k2*exp(-βh*u) - k2r*exp((1-βh)*u) - 4*k3r
c =  k1*exp(-βv*u) + k2r*exp((1-βh)*u) + 2*k3r
```

Resolvida analiticamente com a fórmula de Bhaskara. A raiz fisicamente relevante é a que produz `0 ≤ θ ≤ 1`.

### Relações de Equilíbrio (Balanço Microscópico Detalhado)

Para garantir consistência termodinâmica, as constantes reversas não são parâmetros livres:

```
k2r = (k1 * k2) / k1r
k3r = (k3 * k1^2) / k1r^2
```

Implementadas como expressões no `lmfit`:
```python
params.add("k2r", expr="(k1*k2)/k1r")
params.add("k3r", expr="(k3*k1**2)/(k1r**2)")
```

Isso reduz o número de parâmetros livres e impede soluções termodinamicamente inconsistentes.

---

## 13. Referências

### Métodos Computacionais

- **scipy.optimize.least_squares** (TRF + robust loss):
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html

- **lmfit** — Fitting não-linear sobre scipy:
  https://lmfit.github.io/lmfit-py/

- **Evolução Diferencial** — Storn & Price (1997), *J. Global Optim.*
  DOI: 10.1023/A:1008202821328

### Estatística

- **AIC** — Akaike (1974), *IEEE Trans. Autom. Control*, 19:716.
- **BIC** — Schwarz (1978), *Ann. Statist.*, 6:461.
- **Mínimos Quadrados Robustos** — Huber, P.J. (1981), *Robust Statistics*, Wiley.

### Eletroquímica

- **Mecanismo HER** — Conway & Tilak (2002), *Electrochimica Acta*, 47:3571.
- **Inclinação de Tafel** — Trasatti (1999), *J. Electroanal. Chem.*, 476:90.
- **Balanço Microscópico Detalhado** — Bard & Faulkner, *Electrochemical Methods*, 2nd ed., Ch. 3.
