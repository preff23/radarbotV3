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
  Container,
  Center,
  Grid,
  ThemeIcon,
  RingProgress,
  Skeleton,
  Flex,
  rem,
  useMantineTheme,
  Tabs,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { 
  IconPlus, 
  IconTrash, 
  IconRefresh, 
  IconSearch, 
  IconEdit, 
  IconTrendingUp, 
  IconTrendingDown, 
  IconMinus, 
  IconPhone, 
  IconLogin, 
  IconLogout,
  IconWallet,
  IconChartLine,
  IconCoins,
  IconDiamond,
  IconStar,
  IconArrowUp,
  IconArrowDown,
  IconEye,
  IconSettings,
  IconX,
  IconDashboard,
  IconChartBar
} from '@tabler/icons-react'
import './App.css'
import { MINIAPP_REV } from './version'
import MonitoringDashboard from './components/MonitoringDashboard' 

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

  // Last resort: return null to show login form
  console.log('No user data available, showing login form')
  return null
}

async function apiRequest(path, options = {}, userPhone = null) {
  const userData = getUserData()
  
  // Use userPhone from state if provided, otherwise try Telegram data
  const phone = userPhone || userData?.phone
  const telegramId = userData?.telegram_id
  
  if (!phone) {
    throw new Error('User not authenticated')
  }
  
  const headers = new Headers(options.headers || {})
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  
  // Use phone from parameter or Telegram data
  if (telegramId) {
    headers.set('X-Telegram-Id', telegramId)
  }
  headers.set('X-User-Phone', phone)
  
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

function usePortfolio(userPhone = null) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    if (!userPhone) return
    
    setLoading(true)
    setError(null)
    try {
      const result = await apiRequest('/api/portfolio', {}, userPhone)
      setData(result)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [userPhone])

  const refresh = async () => {
    await fetchData()
    notifications.show({ message: 'Портфель обновлён', color: 'green' })
  }

  return { data, loading, error, refresh }
}

function PhoneConfirmationForm({ detectedPhone, onConfirm, onReject }) {
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!phone.trim()) return

    console.log('=== PHONE CONFIRMATION FORM SUBMIT ===')
    console.log('Original phone input:', phone)
    setLoading(true)
    try {
      // Normalize phone number - remove all non-digits first
      let digitsOnly = phone.replace(/\D/g, '')
      let normalizedPhone = ''
      
      // Handle different formats
      if (digitsOnly.length === 10) {
        // 9151731545 -> +79151731545
        normalizedPhone = '+7' + digitsOnly
      } else if (digitsOnly.length === 11) {
        if (digitsOnly.startsWith('8')) {
          // 89151731545 -> +79151731545
          normalizedPhone = '+7' + digitsOnly.substring(1)
        } else if (digitsOnly.startsWith('7')) {
          // 79151731545 -> +79151731545
          normalizedPhone = '+' + digitsOnly
        } else {
          // Other 11 digits -> +7 + digits
          normalizedPhone = '+7' + digitsOnly
        }
      } else if (digitsOnly.length === 9) {
        // 915173154 -> +7915173154 (incomplete number, but let's try)
        normalizedPhone = '+7' + digitsOnly
      } else {
        // Fallback - just add +7
        normalizedPhone = '+7' + digitsOnly
      }
      
      console.log('Original phone:', phone)
      console.log('Digits only:', digitsOnly)
      console.log('Normalized phone:', normalizedPhone)

      // Try to find user by phone
      console.log('Trying to login with phone:', normalizedPhone)
      const response = await fetch(`/api/portfolio?phone=${encodeURIComponent(normalizedPhone)}`)
      
      console.log('Response status:', response.status)
      const responseText = await response.text()
      console.log('Response text:', responseText)
      
      if (response.ok) {
        onConfirm(normalizedPhone)
        notifications.show({ message: 'Вход выполнен успешно', color: 'green' })
      } else {
        try {
          const errorData = JSON.parse(responseText)
          notifications.show({ message: `Ошибка: ${errorData.detail || 'Пользователь не найден'}`, color: 'red' })
        } catch {
          notifications.show({ message: 'Пользователь с таким номером не найден. Зарегистрируйтесь в боте.', color: 'red' })
        }
      }
    } catch (error) {
      console.error('Login error:', error)
      notifications.show({ message: `Ошибка при входе: ${error.message}`, color: 'red' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container size="sm" py="xl">
      <Center>
        <Card shadow="sm" padding="xl" radius="md" withBorder style={{ width: '100%', maxWidth: 400 }}>
          <Stack gap="md" align="center">
            <Avatar size="xl" color="blue" variant="light">
              <IconPhone size={32} />
            </Avatar>
            <Title order={2} ta="center">Подтвердите номер телефона</Title>
            <Text size="sm" c="dimmed" ta="center">
              Мы определили ваш номер как <Text fw={600} c="blue">{detectedPhone}</Text>
            </Text>
            <Text size="sm" c="dimmed" ta="center">
              Это ваш номер телефона?
            </Text>
            
            <Group gap="md" justify="center">
              <Button
                color="green"
                leftSection={<IconPhone size={16} />}
                onClick={() => onConfirm(detectedPhone)}
              >
                Да, это мой номер
              </Button>
              <Button
                variant="outline"
                color="red"
                onClick={onReject}
              >
                Нет, другой номер
              </Button>
            </Group>
            
            <Divider label="Или введите другой номер" labelPosition="center" />
            
            <form onSubmit={handleSubmit} style={{ width: '100%' }}>
              <Stack gap="md">
                <TextInput
                  label="Номер телефона"
                  placeholder="8 915 173 15 45 или +79151731545"
                  value={phone}
                  onChange={(e) => setPhone(e.currentTarget.value)}
                  leftSection={<IconPhone size={16} />}
                  description="Принимаются любые форматы: 8 915 173 15 45, 79151731545, +79151731545"
                  required
                />
                <Button
                  type="submit"
                  fullWidth
                  leftSection={<IconLogin size={16} />}
                  loading={loading}
                >
                  Войти с этим номером
                </Button>
              </Stack>
            </form>
            
            <Text size="xs" c="dimmed" ta="center">
              Если вы еще не регистрировались, отправьте /start боту
            </Text>
          </Stack>
        </Card>
      </Center>
    </Container>
  )
}

function LoginForm({ onLogin }) {
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    console.log('=== HANDLE SUBMIT CALLED ===')
    console.log('Event:', e)
    console.log('Phone before preventDefault:', phone)
    
    e.preventDefault()
    
    console.log('After preventDefault')
    console.log('Phone trim check:', phone.trim())
    
    if (!phone.trim()) {
      console.log('Phone is empty, returning')
      return
    }

    console.log('=== LOGIN FORM SUBMIT ===')
    console.log('Original phone input:', phone)
    setLoading(true)
    try {
      // Normalize phone number - remove all non-digits first
      let digitsOnly = phone.replace(/\D/g, '')
      let normalizedPhone = ''
      
      // Handle different formats
      if (digitsOnly.length === 10) {
        // 9151731545 -> +79151731545
        normalizedPhone = '+7' + digitsOnly
      } else if (digitsOnly.length === 11) {
        if (digitsOnly.startsWith('8')) {
          // 89151731545 -> +79151731545
          normalizedPhone = '+7' + digitsOnly.substring(1)
        } else if (digitsOnly.startsWith('7')) {
          // 79151731545 -> +79151731545
          normalizedPhone = '+' + digitsOnly
        } else {
          // Other 11 digits -> +7 + digits
          normalizedPhone = '+7' + digitsOnly
        }
      } else if (digitsOnly.length === 9) {
        // 915173154 -> +7915173154 (incomplete number, but let's try)
        normalizedPhone = '+7' + digitsOnly
      } else {
        // Fallback - just add +7
        normalizedPhone = '+7' + digitsOnly
      }
      
      console.log('Original phone:', phone)
      console.log('Digits only:', digitsOnly)
      console.log('Normalized phone:', normalizedPhone)

      // Try to find user by phone
      console.log('Trying to login with phone:', normalizedPhone)
      const response = await fetch(`/api/portfolio?phone=${encodeURIComponent(normalizedPhone)}`)
      
      console.log('Response status:', response.status)
      const responseText = await response.text()
      console.log('Response text:', responseText)
      
      if (response.ok) {
        onLogin(normalizedPhone)
        notifications.show({ message: 'Вход выполнен успешно', color: 'green' })
      } else {
        try {
          const errorData = JSON.parse(responseText)
          notifications.show({ message: `Ошибка: ${errorData.detail || 'Пользователь не найден'}`, color: 'red' })
        } catch {
          notifications.show({ message: 'Пользователь с таким номером не найден. Зарегистрируйтесь в боте.', color: 'red' })
        }
      }
    } catch (error) {
      console.error('Login error:', error)
      notifications.show({ message: `Ошибка при входе: ${error.message}`, color: 'red' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container size="sm" py="xl">
      <Center>
        <Card shadow="sm" padding="xl" radius="md" withBorder style={{ width: '100%', maxWidth: 400 }}>
          <Stack gap="md" align="center">
            <Avatar size="xl" color="blue" variant="light">
              <IconPhone size={32} />
            </Avatar>
            <Title order={2} ta="center">Вход в Radar портфель</Title>
            <Text size="sm" c="dimmed" ta="center">
              Введите номер телефона, который вы использовали при регистрации в боте
            </Text>
            
            <form onSubmit={handleSubmit} style={{ width: '100%' }}>
              <Stack gap="md">
                <TextInput
                  label="Номер телефона"
                  placeholder="8 915 173 15 45 или +79151731545"
                  value={phone}
                  onChange={(e) => setPhone(e.currentTarget.value)}
                  leftSection={<IconPhone size={16} />}
                  description="Принимаются любые форматы: 8 915 173 15 45, 79151731545, +79151731545"
                  required
                />
                <Button
                  type="submit"
                  fullWidth
                  leftSection={<IconLogin size={16} />}
                  loading={loading}
                  onClick={() => {
                    console.log('Button clicked!')
                    console.log('Phone value:', phone)
                    console.log('Loading state:', loading)
                  }}
                >
                  Войти
                </Button>
              </Stack>
            </form>
            
            <Text size="xs" c="dimmed" ta="center">
              Если вы еще не регистрировались, отправьте /start боту
            </Text>
          </Stack>
        </Card>
      </Center>
    </Container>
  )
}

function AccountTabs({ accounts, active, onChange }) {
  // Убираем табы аккаунтов - используем только один портфель
  return null
}

function PortfolioTable({ account, onEdit, onDelete }) {
  const theme = useMantineTheme()
  
  if (!account) {
    return (
      <Card 
        p="xl" 
        radius="xl" 
        style={{ 
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          color: 'white'
        }}
      >
        <Stack gap="lg" align="center">
          <ThemeIcon size={80} radius="xl" variant="light" color="white" style={{ background: 'rgba(255,255,255,0.2)' }}>
            <IconWallet size={40} />
          </ThemeIcon>
          <Stack gap="xs">
            <Text size="xl" fw={700} c="white">Портфель пуст</Text>
            <Text size="md" c="rgba(255,255,255,0.8)">
              Добавьте ценные бумаги, чтобы начать отслеживать свой портфель
            </Text>
          </Stack>
        </Stack>
      </Card>
    )
  }

  const getSecurityIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'bond': return <IconChartLine size={20} />
      case 'stock': return <IconTrendingUp size={20} />
      case 'etf': return <IconCoins size={20} />
      default: return <IconDiamond size={20} />
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
    <ScrollArea style={{ height: '65vh' }} scrollbarSize={6}>
      <Grid gutter="md">
        {account.positions.map((position, index) => (
          <Grid.Col key={position.id} span={12}>
            <Transition
              mounted={true}
              transition="slide-up"
              duration={300}
              timingFunction="ease-out"
              style={{ transitionDelay: `${index * 50}ms` }}
            >
              {(styles) => (
                <Card
                  shadow="xl"
                  padding="lg"
                  radius="xl"
                  style={{
                    ...styles,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    cursor: 'pointer',
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                    border: '1px solid rgba(0,0,0,0.05)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px) scale(1.02)'
                    e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.1)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0) scale(1)'
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  {/* Декоративная полоса сверху */}
                  <Box
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '4px',
                      background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                      borderRadius: '12px 12px 0 0'
                    }}
                  />
                  
                  <Flex justify="space-between" align="flex-start" gap="md">
                    <Stack gap="sm" style={{ flex: 1, minWidth: 0 }}>
                      <Group gap="sm" align="center">
                        <ThemeIcon 
                          size="lg" 
                          radius="xl" 
                          variant="light" 
                          color={getSecurityColor(position.security_type)}
                          style={{ 
                            background: `linear-gradient(135deg, ${theme.colors[getSecurityColor(position.security_type)][6]} 0%, ${theme.colors[getSecurityColor(position.security_type)][4]} 100%)`,
                            color: 'white'
                          }}
                        >
                          {getSecurityIcon(position.security_type)}
                        </ThemeIcon>
                        <Stack gap={2} style={{ flex: 1, minWidth: 0 }}>
                          <Text fw={700} size="lg" c="dark" truncate>
                            {position.name}
                          </Text>
                          <Group gap="xs" align="center">
                            {position.ticker && (
                              <Badge size="sm" variant="light" color="blue" radius="md">
                                {position.ticker}
                              </Badge>
                            )}
                            {position.security_type && (
                              <Badge size="sm" variant="light" color={getSecurityColor(position.security_type)} radius="md">
                                {position.security_type}
                              </Badge>
                            )}
                            {position.fallback && (
                              <Badge size="sm" variant="light" color="orange" radius="md">
                                <IconStar size={12} style={{ marginRight: 4 }} />
                                Fallback
                              </Badge>
                            )}
                          </Group>
                        </Stack>
                      </Group>
                      
                      {position.isin && (
                        <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace', opacity: 0.7 }}>
                          {position.isin}
                        </Text>
                      )}
                    </Stack>

                    <Stack gap="sm" align="flex-end">
                      <Group gap="xs" align="center">
                        <ThemeIcon size="sm" variant="light" color="teal">
                          <IconCoins size={16} />
                        </ThemeIcon>
                        <Text fw={700} size="xl" c="teal">
                          {position.quantity || 0}
                        </Text>
                        <Text fw={500} size="md" c="dimmed">
                          {position.quantity_unit || 'шт'}
                        </Text>
                      </Group>
                      
                      {position.provider && (
                        <Badge size="xs" variant="light" color="gray" radius="md">
                          {position.provider}
                        </Badge>
                      )}

                      <Group gap="xs">
                        <Tooltip label="Редактировать" position="top">
                          <ActionIcon
                            variant="light"
                            color="blue"
                            size="md"
                            radius="xl"
                            onClick={(e) => {
                              e.stopPropagation()
                              onEdit(position)
                            }}
                            style={{ 
                              background: 'rgba(102, 126, 234, 0.1)',
                              border: '1px solid rgba(102, 126, 234, 0.2)'
                            }}
                          >
                            <IconEdit size={18} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="Удалить" position="top">
                          <ActionIcon
                            variant="light"
                            color="red"
                            size="md"
                            radius="xl"
                            onClick={(e) => {
                              e.stopPropagation()
                              onDelete(position)
                            }}
                            style={{ 
                              background: 'rgba(255, 99, 99, 0.1)',
                              border: '1px solid rgba(255, 99, 99, 0.2)'
                            }}
                          >
                            <IconTrash size={18} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Stack>
                  </Flex>
                </Card>
              )}
            </Transition>
          </Grid.Col>
        ))}
      </Grid>
    </ScrollArea>
  )
}

function AddPositionModal({ opened, onClose, accounts, onSubmit, userPhone }) {
  const [tab, setTab] = useState('search')
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [form, setForm] = useState({
    account: 'manual', // Всегда используем manual аккаунт
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
        account: 'manual', // Всегда используем manual аккаунт
        name: '',
        ticker: '',
        isin: '',
        quantity: 1,
        quantity_unit: 'шт',
      })
    }
  }, [opened, accounts])

  const runSearch = async () => {
    console.log('=== RUN SEARCH ===')
    console.log('Search term:', searchTerm)
    console.log('User phone:', userPhone)
    
    if (!searchTerm.trim()) {
      console.log('Search term is empty, returning')
      return
    }
    
    setSearchLoading(true)
    try {
      const url = `/api/portfolio/search?query=${encodeURIComponent(searchTerm.trim())}`
      console.log('Search URL:', url)
      
      const result = await apiRequest(url, {}, userPhone)
      console.log('Search result:', result)
      
      setSearchResults(result.results || [])
    } catch (err) {
      console.error('Search error:', err)
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
    console.log('=== ADD POSITION SUBMIT ===')
    console.log('Form data:', form)
    console.log('Accounts:', accounts)
    
    const accountMeta = accounts.find((acc) => acc.value === form.account)
    console.log('Account meta:', accountMeta)
    
    const payload = {
      account_id: accountMeta?.account_id || 'manual',
      account_name: accountMeta?.label,
      name: form.name,
      ticker: form.ticker,
      isin: form.isin,
      quantity: form.quantity,
      quantity_unit: form.quantity_unit,
    }
    
    console.log('Payload to send:', payload)
    
    try {
      await onSubmit(payload)
    onClose()
    } catch (error) {
      console.error('Error submitting position:', error)
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Добавить бумагу" size="lg" centered>
      <Stack>
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
  console.log('App component rendering...')
  
  const [userPhone, setUserPhone] = useState(null)
  const [showPhoneConfirmation, setShowPhoneConfirmation] = useState(false)
  const [detectedPhone, setDetectedPhone] = useState(null)
  const [activeTab, setActiveTab] = useState('portfolio')

  const handleLogout = () => {
    setUserPhone(null)
    setShowPhoneConfirmation(false)
    setDetectedPhone(null)
    notifications.show({ message: 'Вы вышли из профиля', color: 'blue' })
  }
  
  // Check if user is authenticated
  const telegramData = getUserData()
  const isAuthenticated = userPhone || (telegramData && !showPhoneConfirmation)
  
  console.log('=== AUTH DEBUG ===')
  console.log('userPhone:', userPhone)
  console.log('telegramData:', telegramData)
  console.log('showPhoneConfirmation:', showPhoneConfirmation)
  console.log('isAuthenticated:', isAuthenticated)
  console.log('==================')

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

  // Check if we need to show phone confirmation
  useEffect(() => {
    if (telegramData && !userPhone && !showPhoneConfirmation) {
      setDetectedPhone(telegramData.phone)
      setShowPhoneConfirmation(true)
    }
  }, [telegramData, userPhone, showPhoneConfirmation])
  
  const { data, loading, error, refresh } = usePortfolio(userPhone)
  const accounts = useMemo(() => {
    if (!data?.accounts) return []
    // Всегда используем только manual аккаунт
    const manualAccount = data.accounts.find(acc => acc.account_id === 'manual')
    if (manualAccount) {
      return [{
        value: 'manual',
        account_id: 'manual',
        label: 'Портфель',
        raw: manualAccount,
      }]
    }
    return []
  }, [data])

  const [activeAccount, setActiveAccount] = useState('manual')
  const [addOpened, setAddOpened] = useState(false)
  const [editTarget, setEditTarget] = useState(null)

  useEffect(() => {
    if (accounts.length > 0 && !accounts.some((acc) => acc.value === activeAccount)) {
      setActiveAccount('manual')
    }
  }, [accounts, activeAccount])

  const currentAccount = useMemo(() => {
    if (accounts.length === 0) return null
    const meta = accounts.find((acc) => acc.value === 'manual') || accounts[0]
    return meta.raw
  }, [accounts, activeAccount])

  const handleAdd = async (payload) => {
    try {
      await apiRequest('/api/portfolio/position', {
        method: 'POST',
        body: JSON.stringify(payload),
      }, userPhone)
      notifications.show({ message: 'Позиция добавлена', color: 'green' })
      refresh()
    } catch (err) {
      notifications.show({ message: err.message, color: 'red' })
    }
  }

  const handleDelete = async (position) => {
    try {
      await apiRequest(`/api/portfolio/position/${position.id}`, { method: 'DELETE' }, userPhone)
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
      }, userPhone)
      notifications.show({ message: 'Позиция обновлена', color: 'green' })
      refresh()
    } catch (err) {
      notifications.show({ message: err.message, color: 'red' })
    }
  }

  // Show phone confirmation form if Telegram data is available
  if (showPhoneConfirmation && detectedPhone) {
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
            <Group justify="center" px="md" py="md">
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
                    Подтверждение номера
                  </Text>
                </Stack>
              </Group>
            </Group>
          </AppShell.Header>
          <AppShell.Main>
            <PhoneConfirmationForm 
              detectedPhone={detectedPhone}
              onConfirm={(phone) => {
                setUserPhone(phone)
                setShowPhoneConfirmation(false)
              }}
              onReject={() => {
                setShowPhoneConfirmation(false)
              }}
            />
          </AppShell.Main>
        </AppShell>
      </Stack>
    )
  }

  // Show login form if not authenticated
  if (!isAuthenticated) {
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
            <Group justify="center" px="md" py="md">
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
                    Вход в систему
                  </Text>
                </Stack>
              </Group>
            </Group>
          </AppShell.Header>
          <AppShell.Main>
            <LoginForm onLogin={setUserPhone} />
          </AppShell.Main>
        </AppShell>
      </Stack>
    )
  }

  return (
    <Stack style={{ minHeight: '100vh' }}>
      <AppShell
        padding="md"
        header={{ height: 80 }}
        styles={{ 
          main: { 
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            minHeight: '100vh'
          } 
        }}
      >
        <AppShell.Header
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderBottom: 'none',
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Container size="xl" h="100%">
            <Group justify="space-between" align="center" h="100%">
              <Group gap="md">
                <ThemeIcon 
                  size="xl" 
                  radius="xl" 
                variant="light"
                  color="white"
                  style={{ 
                    background: 'rgba(255,255,255,0.2)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <IconDiamond size={24} />
                </ThemeIcon>
                <Stack gap={2}>
                  <Text size="xl" fw={800} c="white" style={{ letterSpacing: '0.5px' }}>
                    Radar портфель
                  </Text>
                  <Text size="xs" c="rgba(255,255,255,0.7)" style={{ letterSpacing: '0.3px' }}>
                    {data?.user ? `Аккаунт: ${data.user.phone || data.user.telegram_id || 'не определен'}` : 'Загрузка...'}
                  </Text>
                </Stack>
              </Group>
              <Group gap="sm">
                <Button
                  variant={activeTab === 'portfolio' ? 'filled' : 'light'}
                  color="white"
                  size="md"
                  leftSection={<IconWallet size={18} />}
                  onClick={() => setActiveTab('portfolio')}
                  radius="xl"
                  style={{
                    background: activeTab === 'portfolio' ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.15)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: '600',
                    backdropFilter: 'blur(10px)',
                    transition: 'all 0.3s ease'
                  }}
                >
                  Портфель
                </Button>
                <Button
                  variant={activeTab === 'monitoring' ? 'filled' : 'light'}
                  color="white"
                  size="md"
                  leftSection={<IconDashboard size={18} />}
                  onClick={() => setActiveTab('monitoring')}
                  radius="xl"
                  style={{
                    background: activeTab === 'monitoring' ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.15)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: '600',
                    backdropFilter: 'blur(10px)',
                    transition: 'all 0.3s ease'
                  }}
                >
                  Мониторинг
                </Button>
                <Button
                  variant="light"
                  color="white"
                  size="md"
                  leftSection={<IconLogout size={18} />}
                  onClick={handleLogout}
                  radius="xl"
                  style={{
                    background: 'rgba(255,255,255,0.15)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: '600',
                    backdropFilter: 'blur(10px)',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.25)'
                    e.currentTarget.style.transform = 'translateY(-2px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.15)'
                    e.currentTarget.style.transform = 'translateY(0)'
                  }}
                >
                  Выйти
                </Button>
              </Group>
          </Group>
          </Container>
        </AppShell.Header>
        <AppShell.Main>
          <Notifications position="top-center" />
          <Container size="xl" px="md" py="lg">
            {activeTab === 'portfolio' && (
              <>
                {loading && (
                  <Center py="xl">
                    <Stack align="center" gap="md">
                      <Loader size="xl" color="blue" />
                      <Text size="lg" fw={500} c="dimmed">Загрузка портфеля...</Text>
                    </Stack>
                  </Center>
                )}
                {error && (
                  <Alert 
                    color="red" 
                    title="Ошибка" 
                    icon={<IconX size={16} />}
                    radius="xl"
                    style={{ marginBottom: '1rem' }}
                  >
                    {error.message}
                  </Alert>
                )}
                {!loading && !error && data && (
                  <Stack gap="xl">
                    <AccountTabs
                      accounts={accounts}
                      active={activeAccount}
                      onChange={setActiveAccount}
                    />
                    {currentAccount ? (
                      <Stack gap="md">
                        <Card 
                          shadow="xl" 
                          padding="xl" 
                          radius="xl"
                          style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none',
                            color: 'white'
                          }}
                        >
                          <Group justify="space-between" align="center">
                            <Group gap="md">
                              <ThemeIcon 
                                size="xl" 
                                radius="xl" 
                                variant="light" 
                                color="white"
                                style={{ 
                                  background: 'rgba(255,255,255,0.2)',
                                  backdropFilter: 'blur(10px)'
                                }}
                              >
                                <IconWallet size={24} />
                              </ThemeIcon>
                              <Stack gap="xs">
                                <Text size="xl" fw={800} c="white">
                                  Портфель
                                </Text>
                                <Group gap="md">
                                  <Badge
                                    variant="light"
                                    color="white"
                                    size="lg"
                                    style={{ 
                                      background: 'rgba(255,255,255,0.2)',
                                      color: 'white',
                                      fontSize: '12px'
                                    }}
                                  >
                                    {currentAccount.currency || 'RUB'}
                                  </Badge>
                                  <Badge
                                    variant="light"
                                    color="white"
                                    size="lg"
                                    style={{ 
                                      background: 'rgba(255,255,255,0.2)',
                                      color: 'white',
                                      fontSize: '12px'
                                    }}
                                  >
                                    {currentAccount.positions.length} бумаг
                                  </Badge>
                                </Group>
                              </Stack>
                            </Group>
                            {currentAccount.portfolio_value && (
                              <Stack gap="xs" align="flex-end">
                                <Text size="sm" c="rgba(255,255,255,0.8)">Общая стоимость</Text>
                                <Text fw={800} size="xl" c="white">
                                  {currentAccount.portfolio_value.toLocaleString()} ₽
                                </Text>
                              </Stack>
                            )}
                          </Group>
                        </Card>
                        <Group justify="space-between" align="center" mb="md">
                          <Text size="lg" fw={600} c="dark">
                            Позиции портфеля
                          </Text>
                          <Button
                            leftSection={<IconPlus size={16} />}
                            onClick={() => setAddOpened(true)}
                            size="md"
                            radius="xl"
                            style={{
                              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                              border: 'none',
                              color: 'white',
                              fontWeight: '600',
                              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                              transition: 'all 0.3s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.transform = 'translateY(-2px)'
                              e.currentTarget.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.4)'
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = 'translateY(0)'
                              e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)'
                            }}
                          >
                            Добавить бумагу
                          </Button>
                        </Group>
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
              </>
            )}
            
            {activeTab === 'monitoring' && (
              <MonitoringDashboard />
            )}
          </Container>
        </AppShell.Main>
      </AppShell>
      <AddPositionModal
        opened={addOpened}
        onClose={() => setAddOpened(false)}
        accounts={accounts}
        onSubmit={handleAdd}
        userPhone={userPhone}
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
