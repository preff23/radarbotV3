import { useEffect, useMemo, useState } from 'react'
import {
  ActionIcon,
  Alert,
  AppShell,
  Badge,
  Box,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  NumberInput,
  ScrollArea,
  Select,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Title,
  Transition,
  Paper,
  Divider,
  Tooltip,
  Avatar,
  Progress,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { IconPlus, IconTrash, IconRefresh, IconSearch, IconEdit, IconTrendingUp, IconTrendingDown, IconMinus } from '@tabler/icons-react'
import './App.css'
import { MINIAPP_REV } from './version' 

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').trim()

// Get real user data from Telegram WebApp
function getUserData() {
  const tg = window?.Telegram?.WebApp
  console.log('=== Telegram WebApp Debug ===')
  console.log('Telegram WebApp object:', tg)
  console.log('initDataUnsafe:', tg?.initDataUnsafe)
  console.log('user:', tg?.initDataUnsafe?.user)
  console.log('initData:', tg?.initData)
  console.log('================================')
  
  // Try to get user data from Telegram WebApp
  let user = null
  if (tg?.initDataUnsafe?.user) {
    user = tg.initDataUnsafe.user
    console.log('Using initDataUnsafe.user:', user)
  } else if (tg?.initData) {
    try {
      const urlParams = new URLSearchParams(tg.initData)
      const userParam = urlParams.get('user')
      if (userParam) {
        user = JSON.parse(decodeURIComponent(userParam))
        console.log('Parsed user from initData:', user)
      }
    } catch (e) {
      console.error('Error parsing initData:', e)
    }
  }

  // If we have user data from Telegram, use it
  if (user && user.id) {
    return {
      telegram_id: String(user.id),
      phone: user.phone_number || null,
      username: user.username || 'user'
    }
  }

  // Fallback: use data from URL parameters
  const urlParams = new URLSearchParams(window.location.search)
  const tgId = urlParams.get('tg_id') || urlParams.get('telegram_id')
  const phone = urlParams.get('phone') || urlParams.get('phone_number')
  
  if (tgId && phone) {
    console.log('Using URL parameters:', { tgId, phone })
    return {
      telegram_id: String(tgId),
      phone: phone,
      username: 'user'
    }
  }

  // Last resort: use default data for development
  console.log('Using default data for development')
  return {
    telegram_id: '521751895',
    phone: '+79151731545',
    username: 'goretofff'
  }
}

async function apiRequest(path, options = {}) {
  const userData = getUserData()
  const headers = new Headers(options.headers || {})
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  
  // Always use real user data
  headers.set('X-Telegram-Id', userData.telegram_id)
  headers.set('X-User-Phone', userData.phone)
  
  const tg = window?.Telegram?.WebApp
  if (tg && typeof tg.ready === 'function') { 
    try { tg.ready(); } catch (_) {} 
  }
  
  const base = (API_BASE_URL && !API_BASE_URL.startsWith('http:') ? API_BASE_URL : '');
  const apiPath = path.startsWith("/api") ? path : `/api${path}`;
  const url = new URL((base || "") + apiPath, window.location.origin);
  
  // Add user data to query params for proxy compatibility
  try { 
    url.searchParams.set('tg_id', userData.telegram_id)
    url.searchParams.set('phone', userData.phone)
  } catch (_) {}
  
  window.__LAST_API_URL__ = url.toString();
  window.__USER_DATA__ = userData; // For debugging
  
  const response = await fetch(url.toString(), {
    ...options,
    headers,
  })
  
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${text || 'API request failed'} [${response.status}] ${url?.toString?.() || ''}`)
  }
  
  if (response.status === 204) {
    return null
  }
  
  return response.json()
}

function usePortfolio() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiRequest('/api/portfolio')
      setData(result)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const refresh = async () => {
    await fetchData()
    notifications.show({ message: 'Портфель обновлён', color: 'green' })
  }

  return { data, loading, error, refresh }
}

function AccountTabs({ accounts, active, onChange }) {
  if (!accounts || accounts.length === 0) {
    return null
  }

  const tabs = accounts.map((acc) => ({
    value: acc.value,
    label: acc.label,
  }))

  return (
    <SegmentedControl
      fullWidth
      value={active}
      onChange={onChange}
      data={tabs}
      color="teal"
    />
  )
}

function PortfolioTable({ account, onEdit, onDelete }) {
  if (!account) {
    return (
      <Paper p="xl" radius="md" style={{ textAlign: 'center' }}>
        <Stack gap="md">
          <Avatar size="xl" color="gray" variant="light">
            <IconMinus size={32} />
          </Avatar>
          <Text size="lg" fw={500} c="dimmed">Портфель пуст</Text>
          <Text size="sm" c="dimmed">Добавьте ценные бумаги для начала работы</Text>
        </Stack>
      </Paper>
    )
  }

  const getSecurityIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'bond': return '📈'
      case 'stock': return '📊'
      case 'etf': return '📋'
      default: return '💼'
    }
  }

  const getSecurityColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'bond': return 'blue'
      case 'stock': return 'green'
      case 'etf': return 'purple'
      default: return 'gray'
    }
  }

  return (
    <ScrollArea style={{ height: '60vh' }}>
      <Stack gap="sm">
        {account.positions.map((position, index) => (
          <Transition
            key={position.id}
            mounted={true}
            transition="slide-right"
            duration={300}
            timingFunction="ease-out"
            style={{ transitionDelay: `${index * 50}ms` }}
          >
            {(styles) => (
              <Card
                key={position.id}
                shadow="sm"
                padding="md"
                radius="md"
                withBorder
                style={{
                  ...styles,
                  background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
                  border: '1px solid #e9ecef',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'
                }}
              >
                <Group justify="space-between" align="flex-start">
                  <Group gap="md" style={{ flex: 1, minWidth: 0 }}>
                    <Avatar
                      size="lg"
                      color={getSecurityColor(position.security_type)}
                      variant="light"
                      style={{ fontSize: '20px' }}
                    >
                      {getSecurityIcon(position.security_type)}
                    </Avatar>
                    <Stack gap="xs" style={{ flex: 1, minWidth: 0 }}>
                      <Text
                        fw={600}
                        size="md"
                        style={{
                          lineHeight: 1.2,
                          wordBreak: 'break-word',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {position.name}
                      </Text>
                      <Group gap="xs" wrap="wrap">
                        {position.ticker && (
                          <Badge
                            variant="light"
                            color="blue"
                            size="sm"
                            style={{ fontSize: '11px' }}
                          >
                            {position.ticker}
                          </Badge>
                        )}
                        {position.isin && (
                          <Tooltip label={position.isin}>
                            <Badge
                              variant="light"
                              color="gray"
                              size="sm"
                              style={{ fontSize: '10px', maxWidth: '80px' }}
                            >
                              {position.isin.substring(0, 8)}...
                            </Badge>
                          </Tooltip>
                        )}
                        {position.fallback && (
                          <Badge variant="light" color="yellow" size="sm">
                            Справочник
                          </Badge>
                        )}
                      </Group>
                    </Stack>
                  </Group>
                  
                  <Stack gap="xs" align="flex-end">
                    <Group gap="xs">
                      <Text fw={700} size="lg" c="teal">
                        {position.quantity ?? '—'}
                      </Text>
                      <Text size="sm" c="dimmed">
                        {position.quantity_unit || 'шт'}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Tooltip label="Редактировать">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            onEdit(position)
                          }}
                        >
                          <IconEdit size={14} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Удалить">
                        <ActionIcon
                          variant="light"
                          color="red"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            onDelete(position)
                          }}
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Stack>
                </Group>
                
                {position.provider && (
                  <>
                    <Divider my="xs" />
                    <Group justify="space-between" align="center">
                      <Text size="xs" c="dimmed">
                        Источник: {position.provider}
                      </Text>
                      <Badge
                        variant="light"
                        color={getSecurityColor(position.security_type)}
                        size="xs"
                      >
                        {position.security_type || 'неизвестно'}
                      </Badge>
                    </Group>
                  </>
                )}
              </Card>
            )}
          </Transition>
        ))}
      </Stack>
    </ScrollArea>
  )
}

function AddPositionModal({ opened, onClose, accounts, onSubmit }) {
  const [tab, setTab] = useState('search')
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [form, setForm] = useState({
    account: accounts[0]?.value || 'default',
    name: '',
    ticker: '',
    isin: '',
    quantity: 1,
    quantity_unit: 'шт',
  })

  useEffect(() => {
    if (!opened) {
      setTab('search')
      setSearchTerm('')
      setSearchResults([])
      setSearchLoading(false)
      setForm({
        account: accounts[0]?.value || 'default',
        name: '',
        ticker: '',
        isin: '',
        quantity: 1,
        quantity_unit: 'шт',
      })
    }
  }, [opened, accounts])

  const runSearch = async () => {
    if (!searchTerm.trim()) return
    setSearchLoading(true)
    try {
      const result = await apiRequest(`/api/portfolio/search?query=${encodeURIComponent(searchTerm.trim())}`)
      setSearchResults(result.results || [])
    } catch (err) {
      notifications.show({ message: 'Не удалось выполнить поиск', color: 'red' })
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSelectSearchResult = (item) => {
    setForm((prev) => ({
      ...prev,
      name: item.name || prev.name,
      ticker: item.ticker || prev.ticker,
      isin: item.isin || prev.isin,
      quantity: item.quantity ?? prev.quantity,
      quantity_unit: item.quantity_unit || prev.quantity_unit,
    }))
    setTab('manual')
  }

  const handleSubmit = async () => {
    const accountMeta = accounts.find((acc) => acc.value === form.account)
    await onSubmit({
      account_id: accountMeta?.account_id || 'default',
      account_name: accountMeta?.label,
      name: form.name,
      ticker: form.ticker,
      isin: form.isin,
      quantity: form.quantity,
      quantity_unit: form.quantity_unit,
    })
    onClose()
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Добавить бумагу" size="lg" centered>
      <Stack>
        <Select
          label="Счёт"
          data={accounts}
          value={form.account}
          onChange={(value) => setForm((prev) => ({ ...prev, account: value }))}
        />
        <SegmentedControl
          fullWidth
          value={tab}
          onChange={setTab}
          data={[
            { label: 'Поиск', value: 'search' },
            { label: 'Вручную', value: 'manual' },
          ]}
        />

        {tab === 'search' && (
          <Stack>
            <TextInput
              label="Поиск бумаги"
              placeholder="Введите тикер или название"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.currentTarget.value)}
              rightSection={<IconSearch size={16} />}
            />
            <Group>
              <Button onClick={runSearch} loading={searchLoading} leftSection={<IconSearch size={16} />}>
                Найти
              </Button>
              <Button variant="subtle" onClick={() => setTab('manual')}>
                Перейти к ручному вводу
              </Button>
            </Group>
            <Stack gap="sm">
              {searchResults.map((item) => (
                <Box
                  key={`${item.ticker || item.isin || item.name}`}
                  p="sm"
                  style={{
                    border: '1px solid var(--mantine-color-default-border)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleSelectSearchResult(item)}
                >
                  <Group justify="space-between">
                    <Stack gap={2}>
                      <Text fw={500}>{item.name || 'Без названия'}</Text>
                      {item.description && <Text size="sm" c="dimmed">{item.description}</Text>}
                    </Stack>
                    <Group gap="xs">
                      {item.ticker && <Badge color="blue" variant="light">{item.ticker}</Badge>}
                      {item.isin && <Badge color="gray" variant="light">{item.isin}</Badge>}
                    </Group>
                  </Group>
                </Box>
              ))}
            </Stack>
          </Stack>
        )}

        {tab === 'manual' && (
          <Stack>
            <TextInput
              label="Название"
              placeholder="Например, Газпром"
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.currentTarget.value }))}
            />
            <TextInput
              label="Тикер"
              placeholder="GAZP"
              value={form.ticker}
              onChange={(event) => setForm((prev) => ({ ...prev, ticker: event.currentTarget.value }))}
            />
            <TextInput
              label="ISIN"
              placeholder="RU000A0JXE06"
              value={form.isin}
              onChange={(event) => setForm((prev) => ({ ...prev, isin: event.currentTarget.value }))}
            />
            <NumberInput
              label="Количество"
              min={0}
              decimalScale={2}
              value={form.quantity}
              onChange={(value) => setForm((prev) => ({ ...prev, quantity: Number(value) }))}
            />
            <TextInput
              label="Единица измерения"
              value={form.quantity_unit}
              onChange={(event) => setForm((prev) => ({ ...prev, quantity_unit: event.currentTarget.value }))}
            />
          </Stack>
        )}

        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>Отменить</Button>
          <Button onClick={handleSubmit} leftSection={<IconPlus size={16} />}>Сохранить</Button>
        </Group>
      </Stack>
    </Modal>
  )
}

function EditPositionModal({ opened, onClose, position, onSubmit }) {
  const [quantity, setQuantity] = useState(position?.quantity ?? 0)
  const [unit, setUnit] = useState(position?.quantity_unit || 'шт')

  useEffect(() => {
    if (opened && position) {
      setQuantity(position.quantity ?? 0)
      setUnit(position.quantity_unit || 'шт')
    }
  }, [opened, position])

  const handleSubmit = async () => {
    await onSubmit({ quantity, quantity_unit: unit })
    onClose()
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Редактировать позицию" centered>
      <Stack>
        <Text>{position?.name}</Text>
        <NumberInput
          label="Количество"
          min={0}
          decimalScale={2}
          value={quantity}
          onChange={(value) => setQuantity(Number(value))}
        />
        <TextInput
          label="Единица измерения"
          value={unit}
          onChange={(event) => setUnit(event.currentTarget.value)}
        />
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>Отменить</Button>
          <Button onClick={handleSubmit}>Сохранить</Button>
        </Group>
      </Stack>
    </Modal>
  )
}

export default function App() {
  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = window?.Telegram?.WebApp
    if (tg) {
      console.log('Initializing Telegram WebApp...')
      tg.ready()
      tg.expand()
      console.log('Telegram WebApp initialized')
    }
  }, [])

  const { data, loading, error, refresh } = usePortfolio()
  const accounts = useMemo(() => {
    if (!data?.accounts) return []
    return data.accounts.map((acc) => ({
      value: acc.internal_id === null ? 'default' : String(acc.internal_id),
      account_id: acc.account_id,
      label: acc.account_name || `Счёт ${acc.account_id}`,
      raw: acc,
    }))
  }, [data])

  const [activeAccount, setActiveAccount] = useState('default')
  const [addOpened, setAddOpened] = useState(false)
  const [editTarget, setEditTarget] = useState(null)

  useEffect(() => {
    if (accounts.length > 0 && !accounts.some((acc) => acc.value === activeAccount)) {
      setActiveAccount(accounts[0].value)
    }
  }, [accounts, activeAccount])

  const currentAccount = useMemo(() => {
    if (accounts.length === 0) return null
    const meta = accounts.find((acc) => acc.value === activeAccount) || accounts[0]
    return meta.raw
  }, [accounts, activeAccount])

  const handleAdd = async (payload) => {
    try {
      await apiRequest('/api/portfolio/position', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      notifications.show({ message: 'Позиция добавлена', color: 'green' })
      refresh()
    } catch (err) {
      notifications.show({ message: err.message, color: 'red' })
    }
  }

  const handleDelete = async (position) => {
    try {
      await apiRequest(`/api/portfolio/position/${position.id}`, { method: 'DELETE' })
      notifications.show({ message: 'Позиция удалена', color: 'green' })
      refresh()
    } catch (err) {
      notifications.show({ message: err.message, color: 'red' })
    }
  }

  const handleUpdate = async (position, payload) => {
    try {
      await apiRequest(`/api/portfolio/position/${position.id}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
      notifications.show({ message: 'Позиция обновлена', color: 'green' })
      refresh()
    } catch (err) {
      notifications.show({ message: err.message, color: 'red' })
    }
  }

  return (
    <Stack style={{ minHeight: '100vh' }}>
      <AppShell
        padding="md"
        header={{ height: 64 }}
        styles={{ main: { backgroundColor: 'var(--mantine-color-body)' } }}
      >
        <AppShell.Header
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderBottom: 'none',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          }}
        >
          <Group justify="space-between" px="md" py="md">
            <Stack gap={4}>
              <Group gap="sm" align="center">
                <Avatar
                  size="md"
                  color="white"
                  variant="filled"
                  style={{
                    background: 'rgba(255,255,255,0.2)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  📊
                </Avatar>
                <Stack gap={0}>
                  <Title order={3} c="white" style={{ textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>
                    Radar портфель
                  </Title>
                  <Text size="xs" c="rgba(255,255,255,0.8)">
                    {data?.user ? `Аккаунт: ${data.user.phone || data.user.telegram_id || 'не определен'}` : 'Загрузка...'}
                  </Text>
                </Stack>
              </Group>
            </Stack>
            <Group gap="sm">
              <Tooltip label="Обновить данные">
                <Button
                  variant="white"
                  color="dark"
                  size="sm"
                  leftSection={<IconRefresh size={16} />}
                  onClick={refresh}
                  style={{
                    background: 'rgba(255,255,255,0.9)',
                    backdropFilter: 'blur(10px)',
                    border: 'none',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  }}
                >
                  Обновить
                </Button>
              </Tooltip>
              <Tooltip label="Добавить ценную бумагу">
                <Button
                  size="sm"
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setAddOpened(true)}
                  style={{
                    background: 'rgba(255,255,255,0.2)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    color: 'white',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  }}
                >
                  Добавить
                </Button>
              </Tooltip>
            </Group>
          </Group>
        </AppShell.Header>
        <AppShell.Main>
          <Notifications position="top-center" />
          <Box px="md" py="lg">
            {loading && (
              <Group justify="center">
                <Loader color="teal" />
              </Group>
            )}
            {error && (
              <Alert color="red" title="Ошибка">
                {error.message}
              </Alert>
            )}
            {!loading && !error && data && (
              <Stack gap="md">
                <AccountTabs
                  accounts={accounts}
                  active={activeAccount}
                  onChange={setActiveAccount}
                />
                {currentAccount ? (
                  <Stack gap="md">
                    <Card
                      shadow="sm"
                      padding="lg"
                      radius="md"
                      withBorder
                      style={{
                        background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
                        border: '1px solid #e9ecef',
                      }}
                    >
                      <Group justify="space-between" align="center">
                        <Group gap="md">
                          <Avatar
                            size="lg"
                            color="teal"
                            variant="light"
                            style={{ fontSize: '24px' }}
                          >
                            💼
                          </Avatar>
                          <Stack gap={4}>
                            <Text fw={700} size="xl" c="dark">
                              {currentAccount.account_name || 'Портфель'}
                            </Text>
                            <Group gap="md">
                              <Badge
                                variant="light"
                                color="teal"
                                size="lg"
                                leftSection={<IconTrendingUp size={14} />}
                              >
                                {currentAccount.currency || 'RUB'}
                              </Badge>
                              <Badge
                                variant="light"
                                color="blue"
                                size="lg"
                              >
                                {currentAccount.positions.length} бумаг
                              </Badge>
                            </Group>
                          </Stack>
                        </Group>
                        {currentAccount.portfolio_value && (
                          <Stack gap={4} align="flex-end">
                            <Text size="xs" c="dimmed">Общая стоимость</Text>
                            <Text fw={700} size="lg" c="teal">
                              {currentAccount.portfolio_value.toLocaleString()} ₽
                            </Text>
                          </Stack>
                        )}
                      </Group>
                    </Card>
                    <PortfolioTable
                      account={currentAccount}
                      onEdit={(pos) => setEditTarget(pos)}
                      onDelete={handleDelete}
                    />
                  </Stack>
                ) : (
                  <Card
                    shadow="sm"
                    padding="xl"
                    radius="md"
                    withBorder
                    style={{ textAlign: 'center' }}
                  >
                    <Stack gap="md">
                      <Avatar size="xl" color="gray" variant="light">
                        <IconMinus size={32} />
                      </Avatar>
                      <Text size="lg" fw={500} c="dimmed">Портфель пуст</Text>
                      <Text size="sm" c="dimmed">Добавьте ценные бумаги для начала работы</Text>
                    </Stack>
                  </Card>
                )}
              </Stack>
            )}
          </Box>
        </AppShell.Main>
      </AppShell>
      <AddPositionModal
        opened={addOpened}
        onClose={() => setAddOpened(false)}
        accounts={accounts}
        onSubmit={handleAdd}
      />
      <EditPositionModal
        opened={!!editTarget}
        onClose={() => setEditTarget(null)}
        position={editTarget}
        onSubmit={(payload) => editTarget && handleUpdate(editTarget, payload)}
      />
    </Stack>
  )
}
